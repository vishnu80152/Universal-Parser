import argparse
import asyncio
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from Extractor.img_ext.img_ext import ImageExtractor
from Extractor import ext_handler


# ---------------- Logger Setup ---------------- #
class ColorFormatter(logging.Formatter):
    COLORS = {
        "INFO": "\033[36m",    # cyan
        "SUCCESS": "\033[32m", # green
        "WARNING": "\033[33m", # yellow
        "ERROR": "\033[31m",   # red
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        message = super().format(record)
        reset = "\033[0m"
        return f"{color}{message}{reset}"


logging.addLevelName(25, "SUCCESS")


def success(self, message, *args, **kws):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kws)


logging.Logger.success = success

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)


# ---------------- Agent ---------------- #
class ExtractAgent:
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        image_model: str = "qwen3-vl:4b",
        text_model: str = "llama3.2",
    ) -> None:
        self.ollama_host = ollama_host.rstrip("/")
        self.image_model = image_model
        self.text_model = text_model
        self.img_extractor = ImageExtractor(model_name=self.image_model, ollama_host=self.ollama_host)

        logger.info(f"Agent initialized (image_model={self.image_model}, text_model={self.text_model})")

    def _is_url(self, s: str) -> bool:
        return s.startswith("http://") or s.startswith("https://")

    def _check_ollama(self) -> bool:
        try:
            resp = requests.get(f"{self.ollama_host}/api/models")
            if resp.status_code == 200:
                logger.success("Connected to Ollama server")
                return True
            else:
                logger.warning(f"Ollama returned status: {resp.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Could not connect to Ollama at {self.ollama_host}: {e}")
            return False

    def _agg_image_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Basic aggregation: keep per-page entries and a combined text field
        agg = {
            "pages": results,
            "combined_text": None,
            "tables": [],
            "descriptions": [],
            "flowcharts": [],
        }

        texts = []
        for r in results:
            if r.get("ocr_text"):
                texts.append(r["ocr_text"])
            if r.get("table_data"):
                try:
                    # if table_data is JSON string, keep it raw; aggregator just stores
                    agg["tables"].append(r["table_data"])
                except Exception:
                    agg["tables"].append(r.get("table_data"))
            if r.get("image_description"):
                agg["descriptions"].append(r.get("image_description"))
            if r.get("flowchart"):
                agg["flowcharts"].append(r.get("flowchart"))

        if texts:
            agg["combined_text"] = "\n\n".join(texts)

        return agg

    def _summarize_with_llm(self, aggregated: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Use the text_model to produce a structured JSON summary if Ollama is available
        if not self._check_ollama():
            logger.warning("Skipping LLM consolidation because Ollama isn't reachable")
            return None

        prompt = (
            "You are an offline agent using Llama 3.2.\n" "Given the following page-wise extraction JSON, produce a consolidated JSON with keys: 'text', 'tables', 'summary', 'description'.\n" "Return only valid JSON.\n\n" f"DATA:\n{json.dumps(aggregated, indent=2)}\n"
        )

        payload = {
            "model": self.text_model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            r = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=60)
            if r.status_code == 200:
                resp = r.json()
                summary_text = resp.get("response", "")
                try:
                    return json.loads(summary_text)
                except Exception:
                    # If LLM returned non-JSON, wrap it
                    return {"summary": summary_text}
            else:
                logger.error(f"LLM returned status {r.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error calling Ollama LLM: {e}")
            return None

    def process_pdf(self, input_path: str, tmpdir: Path) -> List[Dict[str, Any]]:
        # Convert PDF to images into tmpdir
        logger.info(f"Converting document to images: {input_path}")
        images_out = tmpdir / Path(input_path).stem
        images_out.mkdir(parents=True, exist_ok=True)

        # Lazy import because pdf2image/LibreOffice may not be installed for non-document runs
        try:
            from Extractor.doc_ext.convetr import convert_documents_to_images
        except Exception as e:
            logger.error(f"Document conversion dependencies missing: {e}")
            raise RuntimeError("Document conversion failed due to missing dependencies. Install pdf2image/poppler and libreoffice to enable document conversion.")

        convert_documents_to_images(input_path, str(images_out.parent))

        # The converter saves pages under a folder named after stem
        page_folder = images_out
        if not page_folder.exists():
            # Some fallback: look for folder
            potential = Path(str(images_out.parent)) / Path(input_path).stem
            page_folder = potential

        images = sorted(page_folder.glob("page_*.png"))
        logger.info(f"Found {len(images)} page images in {page_folder}")

        results = []
        for img in images:
            logger.info(f"Extracting from image: {img}")
            data = self.img_extractor.extract_data(str(img))
            results.append({"page": img.name, "result": data})
            logger.success(f"Extracted page {img.name}")
        return results

    def process_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        results = []
        for p in image_paths:
            logger.info(f"Extracting from image: {p}")
            data = self.img_extractor.extract_data(p)
            results.append({"image": Path(p).name, "result": data})
            logger.success(f"Extracted image {p}")
        return results

    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        logger.info(f"Transcribing audio: {audio_path}")
        try:
            transcript = asyncio.run(ext_handler.transcribe_audio(audio_path))
            logger.success("Transcription completed")
            return transcript
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise

    def process_url(self, url: str) -> str:
        logger.info(f"Crawling URL: {url}")
        try:
            raw_md = asyncio.run(ext_handler.crawl(url=url))
            logger.success("Crawl completed")
            return raw_md
        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            raise

    def run(self, input_path: str, output_path: str):
        p = Path(input_path)
        tmpdir = Path(tempfile.mkdtemp(prefix="extract_agent_"))
        logger.info(f"Working in temporary dir: {tmpdir}")

        try:
            aggregated_output: Dict[str, Any] = {"source": input_path}

            if self._is_url(input_path):
                md = self.process_url(input_path)
                aggregated_output["type"] = "url"
                aggregated_output["content"] = md

            elif p.is_dir():
                logger.info(f"Processing directory: {p}")
                images = [str(x) for x in p.rglob("*.png")]
                logger.info(f"Found {len(images)} images in directory")
                images_res = self.process_images(images)
                aggregated_output["type"] = "images_dir"
                aggregated_output["images"] = images_res

            elif p.is_file():
                ext = p.suffix.lower()
                if ext in {".pdf", ".docx", ".pptx"}:
                    logger.info("Detected document file -> converting to images and extracting")
                    results = self.process_pdf(str(p), tmpdir)
                    aggregated = self._agg_image_results([r["result"] for r in results])
                    aggregated_output["type"] = "document"
                    aggregated_output["pages"] = results
                    aggregated_output["aggregated"] = aggregated

                    # Try to consolidate with LLM
                    llm_summary = self._summarize_with_llm(aggregated)
                    if llm_summary:
                        aggregated_output["llm_summary"] = llm_summary

                elif ext in {".png", ".jpg", ".jpeg"}:
                    logger.info("Detected image file -> extracting")
                    res = self.process_images([str(p)])
                    aggregated_output["type"] = "image"
                    aggregated_output["images"] = res

                elif ext in {".wav", ".mp3"}:
                    logger.info("Detected audio file -> transcribing")
                    transcript = self.process_audio(str(p))
                    aggregated_output["type"] = "audio"
                    aggregated_output["transcript"] = transcript

                else:
                    logger.error(f"Unsupported file type: {ext}")
                    raise ValueError(f"Unsupported file type: {ext}")

            else:
                logger.error("Input path not found")
                raise FileNotFoundError(input_path)

            # Save final JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(aggregated_output, f, indent=2)

            logger.success(f"Saved output to {output_path}")

        finally:
            # Clean up
            try:
                shutil.rmtree(tmpdir)
                logger.info("Cleaned up temporary directory")
            except Exception:
                pass


# ---------------- CLI ENTRY ---------------- #

if __name__ == "__main__":
    agent = ExtractAgent()
    agent.run("https://www.synechron.com/en-in/careers/jobs/all/Bengaluru-EC-2_Gateway_campus/all", "etc.json")
