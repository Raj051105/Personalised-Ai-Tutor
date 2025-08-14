import os
import re
from pathlib import Path
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import DATA_DIR, CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL
from utils.text_utils import is_junk
from utils.ocr_utils import ocr_page

BAD_PHRASES = {"lOMoARcPSD", "Downloaded by"}
BIBLIO_HEADINGS = re.compile(r"(?i)^\s*(Text\s*Books?|References?)\s*:?\s*$")
BIBLIO_LINE_PATTERNS = [
    r"\bISBN\b", r"\bPublisher\b", r"\bEdition\b", r"\bAuthor(s)?\b",
    r"\bText\s*Book\b", r"\bReference\b"
]

def clean_text(txt: str) -> str:
    if not txt:
        return ""
    lines = txt.splitlines()
    kept, skip_refs = [], False
    for raw_line in lines:
        line = raw_line.strip()
        if BIBLIO_HEADINGS.match(line):
            skip_refs = True
            continue
        if skip_refs:
            if re.match(r"^[A-Z0-9 ]{5,}$", line) or re.match(r"^\d+[\.\)]", line):
                skip_refs = False
            else:
                continue
        if any(bad in line for bad in BAD_PHRASES):
            continue
        if any(re.search(pat, line, re.IGNORECASE) for pat in BIBLIO_LINE_PATTERNS):
            continue
        kept.append(line)

    cleaned = "\n".join(kept)
    cleaned = cleaned.replace("-\n", "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "\n".join(l.rstrip() for l in cleaned.split("\n"))
    return cleaned.strip()

def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    pages_out = []
    for i, page in enumerate(reader.pages, start=1):
        txt = page.extract_text() or ""
        txt = clean_text(txt)
        if is_junk(txt):
            txt = ocr_page(pdf_path, i)
            txt = clean_text(txt)
        pages_out.append(txt)
    return "\n\n".join(pages_out)

def load_folder(folder: Path, tag: str):
    docs = []
    if not folder.exists():
        return docs
    for fname in os.listdir(folder):
        if fname.lower().endswith(".pdf"):
            fpath = folder / fname
            print(f"📄 {tag.upper():11} | {fname}")
            text = extract_text(fpath)
            docs.append({"text": text, "source": fname, "source_type": tag})
    print(f"Loaded {len(docs)} documents from {tag}")
    return docs

def ingest_all(subject_code: str):
    subject_dir = DATA_DIR / subject_code
    subject_dir.mkdir(parents=True, exist_ok=True)

    all_docs = []
    all_docs += load_folder(subject_dir / "syllabus", "syllabus")
    all_docs += load_folder(subject_dir / "notes", "notes")
    all_docs += load_folder(subject_dir / "past_papers", "past_papers")

    print("DATA_DIR =", DATA_DIR.resolve())
    print("Looking for:", subject_dir.resolve())
    print("Syllabus dir exists?", (subject_dir / "syllabus").exists())
    print("Notes dir exists?", (subject_dir / "notes").exists())
    print("Past_papers dir exists?", (subject_dir / "past_papers").exists())

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks, metas = [], []
    for d in all_docs:
        for chunk in splitter.split_text(d["text"]):
            if chunk.strip():
                chunks.append(chunk)
                metas.append({
                    "subject_code": subject_code,
                    "source": d["source"],
                    "source_type": d["source_type"]
                })

    persist_dir = CHROMA_DIR / subject_code
    persist_dir.mkdir(parents=True, exist_ok=True)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma.from_texts(chunks, embeddings, metadatas=metas, persist_directory=str(persist_dir))
    print(f"✅ {len(chunks)} chunks stored in vector DB for {subject_code}")
    return db