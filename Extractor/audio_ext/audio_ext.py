from faster_whisper import WhisperModel
from typing import List, Dict
import logging
from halo import Halo
from colorama import Fore, Style, init

init(autoreset=True)

# ---------------- LOGGER SETUP ---------------- #

class ColorFormatter(logging.Formatter):
    COLORS = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

logging.addLevelName(25, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(25):
        self._log(25, message, args, **kws)

logging.Logger.success = success

logger = logging.getLogger("audio-transcriber")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)

# ---------------- TRANSCRIBER ---------------- #

class AudioTranscriber:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
    ):
        """
        model_size: tiny | base | small | medium | large
        device: cpu | cuda
        compute_type: int8 | float16 | float32
        language: force language (e.g. 'en') or None for auto-detect
        """
        logger.info(f"Loading Whisper model [{model_size}] on {device}")

        spinner = Halo(
            text="Initializing Whisper model",
            spinner="dots",
            color="cyan"
        )
        spinner.start()

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
            self.language = language
            spinner.succeed("Model loaded successfully")
            logger.success("Whisper model ready")

        except Exception as e:
            spinner.fail("Failed to load model")
            logger.error(str(e))
            raise

    def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe an audio file and return text + segments.
        """
        logger.info(f"Starting transcription: {audio_path}")

        spinner = Halo(
            text="Transcribing audio",
            spinner="dots",
            color="cyan"
        )
        spinner.start()

        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
            )

            text_segments: List[Dict] = []
            full_text = []

            for segment in segments:
                text_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                })
                full_text.append(segment.text.strip())

            spinner.succeed("Transcription completed")
            logger.success(
                f"Detected language: {info.language} | Duration: {info.duration:.2f}s"
            )

            return {
                "language": info.language,
                "duration": info.duration,
                "text": " ".join(full_text),
                "segments": text_segments,
            }

        except Exception as e:
            spinner.fail("Transcription failed")
            logger.error(str(e))
            raise

# ---------------- ENTRY ---------------- #

if __name__ == "__main__":
    transcriber = AudioTranscriber(
        model_size="base",
        device="cpu",
    )

    result = transcriber.transcribe(
        "/home/zoro/DEV/chatbot/sample_data/harvard.wav"
    )

    print("\nFull Transcript:\n")
    print(result["text"])

    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])

    logger.success("Transcript saved to transcript.txt")
