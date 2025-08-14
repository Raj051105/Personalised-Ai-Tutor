import os
from collections import Counter
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# — CONFIG — 
POPPLER = r"C:\Program Files\poppler\Library\bin"          # <- adjust
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DATA_DIR = "data"                                          # base data folder
CHROMA_DIR = "chroma_db"                                   # persistent DB

# — UTILITY — 
def is_junk(text:str, min_len:int=50, dup_thresh:float=0.25)->bool:
    if not text.strip() or len(text) < min_len: return True
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    line_counts = Counter(lines)
    if line_counts and line_counts.most_common(1)[0][1]/len(lines) > dup_thresh:
        return True
    uniq_ratio = len(set(text.split()))/max(len(text.split()),1)
    return uniq_ratio < 0.30

def ocr_page(pdf_path, page_no):
    img = convert_from_path(pdf_path, first_page=page_no, last_page=page_no,
                            poppler_path=POPPLER, fmt="ppm")[0]
    return pytesseract.image_to_string(img, lang="eng").strip()

def extract_text(pdf_path)->str:
    reader = PdfReader(pdf_path)
    out = []
    for i, page in enumerate(reader.pages, start=1):
        txt = page.extract_text() or ""
        if is_junk(txt):                                  # fallback to OCR
            txt = ocr_page(pdf_path, i)
        out.append(txt)
    return "\n".join(out)

# — LOADER — 
def load_folder(folder:str, tag:str):
    docs = []
    for fname in os.listdir(folder):
        if fname.lower().endswith(".pdf"):
            fpath = os.path.join(folder, fname)
            print(f"📄 {tag.upper():11} | {fname}")
            docs.append({
                "text":  extract_text(fpath),
                "source": fname,
                "source_type": tag          # critical for later filters
            })
    return docs

# — INGEST — 
all_docs = []
all_docs += load_folder(os.path.join(DATA_DIR,"syllabus"),     "syllabus")
all_docs += load_folder(os.path.join(DATA_DIR,"notes"),        "notes")
all_docs += load_folder(os.path.join(DATA_DIR,"past_papers"),  "past_papers")

splitter   = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks, metas = [], []
for d in all_docs:
    for chunk in splitter.split_text(d["text"]):
        chunks.append(chunk)
        metas.append({"source": d["source"], "source_type": d["source_type"]})

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma.from_texts(chunks, embeddings, metadatas=metas, persist_directory=CHROMA_DIR)
print(f"✅ {len(chunks)} chunks stored across syllabus, notes, past papers")

# — RETRIEVAL — 
db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

def get_context_scoped(query:str, k:int=6, sources:list|None=None)->str:
    """Return newline-separated winning chunks, optionally filtered by source_type list."""
    results = db.similarity_search_with_relevance_scores(query, k=20)  # wide net
    hits = [r for r,score in results if (sources is None or r.metadata['source_type'] in sources)]
    hits = hits[:k]
    return "\n\n".join(h.page_content for h in hits)

# Example: fundamentals first (syllabus + notes)
context_fund = get_context_scoped(
    "CS8491 basics of computer architecture", k=7,
    sources=["syllabus","notes"]
)

# Example: exam style (past papers only)
context_exam = get_context_scoped(
    "CS8491 question trends cache memory", k=5,
    sources=["past_papers"]
)

# Example query
context = get_context("Anna University Regulation 2021 CS8491 Computer Architecture")
print("Retrieved Context:\n", context[:500])

def generate_mcqs(student_info, context):
    prompt = f"""
            You are a question paper generator.  
            Given the following extracted exam content, create **original** multiple-choice questions (MCQs) based solely on the concepts in the text.

            Rules:
            - Generate ONLY new MCQs, do not answer them.
            - Avoid copying exact wording from the text; rephrase concepts.
            - Each MCQ must have 4 options: A, B, C, D.
            - Randomize the position of the correct answer.
            - Provide the correct answer key separately.
            - Output format must be JSON like this:

            [
            {{
                "question": "Which algorithm is used for ...?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_option": "B"
            }},
            ...
            ]

            Student info: {student_info}

            Context:
            \"\"\"{context}\"\"\"

            Generate exactly 5 MCQs from the above context.
            """
    print(prompt)
    result = subprocess.run(
        ["ollama", "run", "llama3.1:8b", prompt],
        capture_output=True, text=True
    )
    return result.stdout

# Example usage
student_info = {
    "name": "John Doe",
    "age": 19,
    "batch": "2023-2027",
    "subject_code": "CS8491",
    "regulation": "R2021"
}

output = generate_mcqs(student_info, context)
print("Generated Questions:\n", output)