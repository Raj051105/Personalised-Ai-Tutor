from pathlib import Path
from langchain_chroma import Chroma
from config import CHROMA_DIR, EMBEDDING_MODEL
from langchain_huggingface import HuggingFaceEmbeddings

def load_db(subject_code: str):
    persist_dir = CHROMA_DIR / subject_code
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings
    )

def get_context_scoped(query: str, subject_code: str, k: int = 6, sources=None) -> str:
    db = load_db(subject_code)
    results = db.similarity_search(query, k=20)
    hits = [r for r in results if (sources is None or r.metadata.get("source_type") in sources)]

    if not hits and sources is not None:
        print(f"⚠️ No matches for {sources}, retrying without filter")
        hits = results

    return "\n\n".join(h.page_content for h in hits[:k])