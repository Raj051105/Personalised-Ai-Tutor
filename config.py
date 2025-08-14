# config.py
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR        = BASE_DIR / "data"
CHROMA_DIR      = BASE_DIR / "chroma_db"
SYLLABUS_DIR    = DATA_DIR / "syllabus"
NOTES_DIR       = DATA_DIR / "notes"
PAST_PAPERS_DIR = DATA_DIR / "past_papers"


# Poppler (Windows)
POPPLER_PATH    = r"C:\Program Files\poppler\Library\bin"

# Tesseract (Windows)
TESSERACT_PATH  = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Chunk settings
CHUNK_SIZE      = 1000
CHUNK_OVERLAP   = 200

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Ollama LLM model
OLLAMA_MODEL    = "llama3.1:8b"