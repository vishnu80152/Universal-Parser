# Universal Parser

A powerful offline-first extraction agent that processes multiple data formats including documents, images, audio files, and web content. Built with local LLM support via Ollama for privacy-focused data extraction.

## Features

- **Multi-Format Support**: Process PDFs, DOCX, PPTX, images, audio files, and web URLs
- **Offline Processing**: Uses local Ollama models for complete data privacy
- **Vision-Language Models**: Leverages Qwen3-VL for advanced image understanding
- **OCR & Table Extraction**: Automatically extracts text and structured table data
- **Audio Transcription**: Transcribe audio files (WAV, MP3)
- **Web Crawling**: Extract and convert web content to markdown
- **Batch Processing**: Handle directories with multiple files
- **LLM-Powered Summarization**: Consolidate extracted data with intelligent summaries

## Architecture

```
Universal Parser
├── Document Processing
│   ├── PDF → Images → Extraction
│   ├── DOCX → Images → Extraction
│   └── PPTX → Images → Extraction
├── Image Processing
│   ├── OCR Text Extraction
│   ├── Table Detection & Extraction
│   ├── Image Description
│   └── Flowchart Recognition
├── Audio Processing
│   └── Speech-to-Text Transcription
└── Web Processing
    └── URL Crawling & Markdown Conversion
```

## Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Poppler (for PDF processing)
- LibreOffice (for DOCX/PPTX conversion)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils libreoffice
```

**macOS:**
```bash
brew install poppler libreoffice
```

**Windows:**
- Download and install [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/)
- Download and install [LibreOffice](https://www.libreoffice.org/download/download/)

### Setup Ollama Models

```bash
# Pull the vision model
ollama pull qwen3-vl:4b

# Pull the text model
ollama pull llama3.2
```

## Usage

### Basic Usage

```python
from agent import ExtractAgent

# Initialize the agent
agent = ExtractAgent(
    ollama_host="http://localhost:11434",
    image_model="qwen3-vl:4b",
    text_model="llama3.2"
)

# Process a document
agent.run("document.pdf", "output.json")
```

### Command Line

```bash
python agent.py
```

**Note:** Edit the script's `__main__` section to specify your input and output paths.

### Supported Input Types

#### Documents
```python
agent.run("document.pdf", "output.json")
agent.run("presentation.pptx", "output.json")
agent.run("report.docx", "output.json")
```

#### Images
```python
# Single image
agent.run("screenshot.png", "output.json")

# Directory of images
agent.run("/path/to/images/", "output.json")
```

#### Audio
```python
agent.run("recording.wav", "output.json")
agent.run("podcast.mp3", "output.json")
```

#### Web URLs
```python
agent.run("https://example.com/page", "output.json")
```

## Output Format

The agent produces structured JSON output with the following schema:

### Document Output
```json
{
  "source": "document.pdf",
  "type": "document",
  "pages": [
    {
      "page": "page_1.png",
      "result": {
        "ocr_text": "Extracted text...",
        "table_data": {...},
        "image_description": "Description...",
        "flowchart": {...}
      }
    }
  ],
  "aggregated": {
    "combined_text": "All pages combined...",
    "tables": [...],
    "descriptions": [...],
    "flowcharts": [...]
  },
  "llm_summary": {
    "text": "Consolidated text",
    "tables": [...],
    "summary": "AI-generated summary",
    "description": "Overall description"
  }
}
```

### Image Output
```json
{
  "source": "image.png",
  "type": "image",
  "images": [
    {
      "image": "image.png",
      "result": {
        "ocr_text": "...",
        "table_data": {...},
        "image_description": "..."
      }
    }
  ]
}
```

### Audio Output
```json
{
  "source": "audio.wav",
  "type": "audio",
  "transcript": {
    "text": "Transcribed content...",
    "segments": [...]
  }
}
```

### URL Output
```json
{
  "source": "https://example.com",
  "type": "url",
  "content": "# Markdown Content\n..."
}
```

## Configuration

### Custom Models

```python
agent = ExtractAgent(
    ollama_host="http://localhost:11434",
    image_model="llava:latest",  # Use different vision model
    text_model="mistral:latest"   # Use different text model
)
```

### Remote Ollama Server

```python
agent = ExtractAgent(
    ollama_host="http://192.168.1.100:11434"
)
```

## Features in Detail

### Image Extraction
- **OCR**: Extracts all visible text from images
- **Table Detection**: Identifies and structures tabular data
- **Image Description**: Generates natural language descriptions
- **Flowchart Recognition**: Detects and describes flowcharts and diagrams

### Document Processing
- Converts documents to high-quality images
- Processes each page independently
- Aggregates results across all pages
- Provides LLM-powered consolidation

### Audio Transcription
- Supports WAV and MP3 formats
- Async processing for efficiency
- Detailed transcription output

### Web Crawling
- Converts web pages to clean markdown
- Preserves structure and formatting
- Handles dynamic content

## Logging

The agent uses colored console logging:

- 🔵 **INFO**: General information
- 🟢 **SUCCESS**: Successful operations
- 🟡 **WARNING**: Warnings and non-critical issues
- 🔴 **ERROR**: Errors and failures

## Error Handling

The agent includes comprehensive error handling:

- Validates Ollama connectivity
- Handles missing dependencies gracefully
- Provides clear error messages
- Automatic cleanup of temporary files

## Limitations

- Requires Ollama to be running for image and LLM processing
- Document conversion requires LibreOffice installation
- PDF processing requires Poppler utilities
- Processing large documents may be memory-intensive
- LLM quality depends on the chosen Ollama models

## Dependencies

### Core
- `requests` - HTTP client for Ollama API
- `asyncio` - Async processing support

### Document Processing
- `pdf2image` - PDF to image conversion
- `poppler` - PDF rendering engine
- LibreOffice - DOCX/PPTX conversion

### Custom Modules
- `Extractor.img_ext.img_ext` - Image extraction engine
- `Extractor.ext_handler` - Audio and web handlers

## Contributing

Contributions are welcome! Areas for improvement:

- Additional file format support
- Performance optimizations
- Enhanced error recovery
- More extraction capabilities
- Better LLM prompt engineering

## Author

**Vishnu**
- Email: vishnu80152@gmail.com
- Website: [Portfolio](https://vishnu-ai-nexus-sphere.lovable.app/)

## Acknowledgments

- Built with [Ollama](https://ollama.ai/)
- Uses Qwen3-VL for vision tasks
- Uses Llama 3.2 for text processing

## Support

For issues and questions:
- Check Ollama is running: `ollama list`
- Verify system dependencies are installed
- Check logs for detailed error messages
- Ensure sufficient disk space for temporary files

---

**Universal Parser** - Extract intelligence from any format, completely offline.
