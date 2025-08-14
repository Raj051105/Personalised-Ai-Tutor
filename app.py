from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
import shutil
from ingest import ingest_all
from retriever import get_context_scoped
from mcq_generator import generate_mcqs
from flashcard_generator import generate_flashcards

# ====== Config ======
DATA_DIR = Path("data")
ALLOWED_SUBJECTS = ["CS3491", "MA3251"]  # extend as needed

# Ensure base data dir exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Adaptive Learning Demo API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo, allow all. For prod, restrict to your frontend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
# ====== Routes ======
@app.get("/subjects")
def list_subjects():
    """List allowed subjects"""
    return {"subjects": ALLOWED_SUBJECTS}

@app.post("/upload/{subject_code}")
async def upload_pdf(subject_code: str,
    category: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a PDF to a given subject/category."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")
    if category not in ["syllabus", "notes", "past_papers"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    save_dir = DATA_DIR / subject_code / category
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "saved", "subject_code": subject_code, "category": category,
            "path": str(save_path)}

@app.post("/ingest/{subject_code}")
def ingest_subject(subject_code: str):
    
    """Run ingestion for this subject (syllabus+notes+past_papers)."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")
    ingest_all(subject_code)

    return {"status": "ingested", "subject_code": subject_code}

@app.post("/generate/mcqs/{subject_code}")
def generate_mcqs_api(subject_code: str, query: str):
    """Generate MCQs for a given subject/query from notes+syllabus."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")

    context = get_context_scoped(query, subject_code, k=8, sources=["notes", "syllabus"])
    mcqs = generate_mcqs({"subject_code": subject_code}, context) or []
    return {"subject_code": subject_code, "mcqs": mcqs}

@app.post("/generate/flashcards/{subject_code}")
def generate_flashcards_api(subject_code: str, query: str, num_cards: int = 8):
    """Generate flashcards for a given subject/query from notes+syllabus."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")

    context = get_context_scoped(query, subject_code, k=8, sources=["notes", "syllabus"])
    cards = generate_flashcards({"subject_code": subject_code}, context, num_cards) or []
    return {"subject_code": subject_code, "flashcards": cards}

# Add these routes to your app.py

@app.get("/status/{subject_code}")
def get_subject_status(subject_code: str):
    """Check if a subject has been ingested and what files are available."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")
    
    # Check if vector database exists
    chroma_path = Path(f"chroma_dbs/{subject_code}")
    is_ingested = chroma_path.exists() and any(chroma_path.iterdir())
    
    # Check available files
    subject_path = DATA_DIR / subject_code
    files = {}
    
    for category in ["syllabus", "notes", "past_papers"]:
        category_path = subject_path / category
        if category_path.exists():
            files[category] = [f.name for f in category_path.glob("*.pdf")]
        else:
            files[category] = []
    
    return {
        "subject_code": subject_code,
        "is_ingested": is_ingested,
        "files": files,
        "total_files": sum(len(file_list) for file_list in files.values())
    }

@app.delete("/files/{subject_code}/{category}/{filename}")
def delete_file(subject_code: str, category: str, filename: str):
    """Delete a specific uploaded file."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")
    
    if category not in ["syllabus", "notes", "past_papers"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    file_path = DATA_DIR / subject_code / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(file_path)
        return {"status": "deleted", "file": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "message": "API is running"}

@app.post("/validate/query/{subject_code}")
def validate_query(subject_code: str, query: str):
    """Validate if a query can generate meaningful results."""
    if subject_code not in ALLOWED_SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject_code")
    
    # Check if subject is ingested
    chroma_path = Path(f"chroma_dbs/{subject_code}")
    if not (chroma_path.exists() and any(chroma_path.iterdir())):
        return {
            "valid": False,
            "reason": "Subject documents not processed yet",
            "suggestion": "Please upload and process documents first"
        }
    
    # Try to get some context
    try:
        context = get_context_scoped(query, subject_code, k=3, sources=["notes", "syllabus"])
        if not context or len(context.strip()) < 50:
            return {
                "valid": False,
                "reason": "No relevant content found for this query",
                "suggestion": "Try a broader topic or check if relevant documents are uploaded"
            }
        
        return {
            "valid": True,
            "context_length": len(context),
            "message": "Query looks good for content generation"
        }
    except Exception as e:
        return {
            "valid": False,
            "reason": f"Error processing query: {str(e)}",
            "suggestion": "Please try a different query"
        }

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend application."""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found")

@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    """Alternative endpoint to serve the frontend."""
    return await serve_frontend()

# Optional: Serve the HTML file directly
@app.get("/index.html", response_class=FileResponse)
async def serve_index():
    """Serve the index.html file directly."""
    file_path = "static/index.html"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Health check endpoint (already suggested in previous response)
@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "message": "API is running", "frontend": "available"}