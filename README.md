# Adaptive Learning RAG API

A **Retrieval-Augmented Generation (RAG)** system that generates personalized MCQs and flashcards from uploaded course materials using AI. Built with FastAPI and powered by Ollama for local LLM inference.

## 🚀 Features

- **Subject-Agnostic**: Handle multiple subjects with isolated vector databases
- **Multi-Format Support**: Upload syllabus, notes, and past papers as PDFs
- **Smart Text Extraction**: OCR fallback for scanned documents
- **Content Filtering**: Removes bibliographic references to focus on concepts
- **Dual Generation**: Create both MCQs and flashcards from the same content
- **RESTful API**: Clean JSON responses for easy frontend integration


## 📋 Prerequisites

### System Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/download) installed and running
- Tesseract OCR
- Poppler utilities


### Install System Dependencies

**Windows:**

```bash
# Download and install Tesseract OCR from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Download Poppler from:
# https://github.com/oschwartz10612/poppler-windows/releases
# Add both to your PATH
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install tesseract-ocr poppler-utils
```

**macOS:**

```bash
brew install tesseract poppler
```


## 🛠️ Installation

1. **Clone the repository:**

```bash
git clone <your-repo-url>
cd adaptive-learning-rag
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up Ollama:**

```bash
# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull llama2  # or your preferred model
```

5. **Configure the application:**
    - Update `config.py` with your preferred model and settings
    - Ensure `OLLAMA_MODEL` matches your pulled model

## 🏃 Quick Start

1. **Start the API server:**

```bash
uvicorn app:app --reload
```

2. **Upload documents for a subject:**

```bash
# Upload syllabus
curl -F "category=syllabus" -F "file=@syllabus.pdf" \
     http://127.0.0.1:8000/upload/CS3491

# Upload notes
curl -F "category=notes" -F "file=@unit1.pdf" \
     http://127.0.0.1:8000/upload/CS3491
```

3. **Ingest the documents:**

```bash
curl -X POST http://127.0.0.1:8000/ingest/CS3491
```

4. **Generate content:**

```bash
# Generate MCQs
curl -X POST "http://127.0.0.1:8000/generate/mcqs/CS3491?query=AI%20fundamentals"

# Generate Flashcards
curl -X POST "http://127.0.0.1:8000/generate/flashcards/CS3491?query=neural%20networks&num_cards=5"
```


## 📁 Project Structure

```
Personalised-Ai-Tutor/
├── Notes/                         # External notes directory
└── RAG-backend/                   # Main application directory
    ├── chroma_db/                 # Vector database storage
    │   └── CS3491/                # Subject-specific vector DB
    │       └── 94d8adf8-80bf-427d-a5ac-16e330b6a5ff/  # ChromaDB collection
    ├── data/                      # Document storage by subject
    │   └── CS3491/                # Example subject folder
    │       ├── notes/             # Lecture notes and study materials
    │       ├── past_papers/       # Previous exam papers
    │       └── syllabus/          # Course syllabus documents
    ├── static/                    # Static web assets (CSS, JS, images)
    ├── test/                      # Test files and fixtures
    ├── utils/                     # Utility modules
    │   └── __pycache__/          # Python bytecode cache
    └── __pycache__/              # Main application bytecode cache
```


## 🔧 API Endpoints

| Method | Endpoint | Description |
| :-- | :-- | :-- |
| `GET` | `/subjects` | List available subjects |
| `POST` | `/upload/{subject_code}` | Upload PDF documents |
| `POST` | `/ingest/{subject_code}` | Process documents into vector DB |
| `POST` | `/generate/mcqs/{subject_code}` | Generate MCQs |
| `POST` | `/generate/flashcards/{subject_code}` | Generate flashcards |

See the [API Documentation](docs/api.md) for detailed endpoint specifications.

## 🎯 Usage Examples

### Python Client Example

```python
import requests

# Upload a document
files = {'file': open('notes.pdf', 'rb')}
data = {'category': 'notes'}
response = requests.post('http://127.0.0.1:8000/upload/CS3491', 
                        files=files, data=data)

# Generate MCQs
params = {'query': 'machine learning algorithms'}
response = requests.post('http://127.0.0.1:8000/generate/mcqs/CS3491', 
                        params=params)
mcqs = response.json()['mcqs']
```


### Frontend Integration

```javascript
// Generate flashcards
const query = 'neural networks';
const response = await fetch(`/generate/flashcards/CS3491?query=${query}`, {
    method: 'POST'
});
const data = await response.json();
console.log(data.flashcards);
```


## ⚙️ Configuration

Key configuration options in `config.py`:

```python
# Model Settings
OLLAMA_MODEL = "llama2"  # Your Ollama model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Text Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Paths
DATA_DIR = Path("data")
CHROMA_DIR = Path("chroma_dbs")
```


## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

Use the Postman collection in `tests/postman/` for API testing.

## 🚀 Production Deployment

1. **Use a production ASGI server:**

```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Environment variables:**

```bash
export OLLAMA_MODEL=llama2
export DATA_DIR=/app/data
export CHROMA_DIR=/app/chroma_dbs
```

3. **Docker deployment** (optional):

```bash
docker build -t adaptive-learning-rag .
docker run -p 8000:8000 adaptive-learning-rag
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔍 Troubleshooting

### Common Issues

**Empty generation results:**

- Ensure documents are properly ingested
- Try broader query terms
- Check Ollama model is running: `ollama list`

**OCR not working:**

- Verify Tesseract installation: `tesseract --version`
- Check Poppler installation: `pdftoppm -h`

**CORS errors in frontend:**

- Ensure CORS middleware is enabled in `app.py`
- Check frontend and API URLs match

**Import errors:**

- Activate virtual environment
- Reinstall requirements: `pip install -r requirements.txt`


### Performance Tips

- Use smaller chunk sizes for faster processing
- Limit context retrieval with lower `k` values
- Consider using faster embedding models for large datasets


## 📞 Support

- Create an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide system information and error logs when reporting bugs

***

**Built with ❤️ using FastAPI, LangChain, and Ollama**
