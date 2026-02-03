import subprocess
from pathlib import Path
import logging
from pdf2image import convert_from_path
from halo import Halo
from colorama import Fore, Style, init

init(autoreset=True)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx"}

# ---------------- LOGGER SETUP ---------------- #

class ColorFormatter(logging.Formatter):
    COLORS = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

logging.addLevelName(25, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kws)

logging.Logger.success = success

logger = logging.getLogger("doc2img")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)

# ---------------- CORE LOGIC ---------------- #

def convert_documents_to_images(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        _handle_single_file(input_path, output_dir)
        return

    if input_path.is_dir():
        files = [
            f for f in input_path.rglob("*")
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        logger.info(f"Found {len(files)} documents")

        for file in files:
            rel = file.relative_to(input_path)
            out_folder = output_dir / rel.parent / file.stem
            out_folder.mkdir(parents=True, exist_ok=True)
            _process_file(file, out_folder)
        return

    raise ValueError("Input path does not exist")

def _handle_single_file(file_path, output_dir):
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type")

    out_folder = output_dir / file_path.stem
    out_folder.mkdir(parents=True, exist_ok=True)
    _process_file(file_path, out_folder)

def _process_file(file_path, output_folder):
    spinner = Halo(
        text=f"Processing {file_path.name}",
        spinner="dots",
        color="cyan"
    )
    spinner.start()

    try:
        if file_path.suffix.lower() == ".pdf":
            _pdf_to_images(file_path, output_folder)
        else:
            _office_to_images(file_path, output_folder)

        spinner.succeed(f"Converted {file_path.name}")
        logger.success(f"Saved images to {output_folder}")

    except Exception as e:
        spinner.fail(f"Failed {file_path.name}")
        logger.error(str(e))

def _office_to_images(file_path, output_folder):
    temp_pdf = output_folder / f"{file_path.stem}.pdf"

    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_folder),
            str(file_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _pdf_to_images(temp_pdf, output_folder)
    temp_pdf.unlink(missing_ok=True)

def _pdf_to_images(pdf_path, output_folder):
    images = convert_from_path(pdf_path)
    for i, img in enumerate(images, start=1):
        img.save(output_folder / f"page_{i:03d}.png", "PNG")

# ---------------- ENTRY ---------------- #

if __name__ == "__main__":
    convert_documents_to_images(
        "/home/zoro/DEV/chatbot/sample_data/machine_learning.pdf",
        "output"
    )
