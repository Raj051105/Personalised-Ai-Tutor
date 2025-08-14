import os
import subprocess
import json
import re
from textwrap import dedent
from config import OLLAMA_MODEL

MAX_CONTEXT_CHARS = 12000  # safety guard

def repair_json_string(bad_json: str) -> str:
    """Extract and repair common JSON issues from LLM output."""
    match = re.search(r"\[.*\]", bad_json, re.DOTALL)
    json_part = match.group(0) if match else bad_json
    json_part = re.sub(r"[\x00-\x1F\x7F]", " ", json_part)   # remove control chars
    json_part = re.sub(r",\s*(\]|\})", r"\1", json_part)     # remove trailing commas
    return json_part.strip()

def validate_flashcard_list(cards):
    """
    Ensure each flashcard has both 'front' and 'back' strings
    and no duplicates. Return cleaned list.
    """
    cleaned = []
    seen_fronts = set()

    for card in cards:
        if not isinstance(card, dict):
            continue
        if "front" not in card or "back" not in card:
            continue
        f_text = card["front"].strip()
        b_text = card["back"].strip()
        if not f_text or not b_text:
            continue
        if f_text in seen_fronts:
            continue
        seen_fronts.add(f_text)
        cleaned.append({"front": f_text, "back": b_text})

    return cleaned

def generate_flashcards(student_info: dict, context: list | dict | str, num_cards: int = 10):
    """Generate clean flashcards list from retrieval context (docs, dicts, or string)."""

    # --- Convert context to string if it's list of docs/dicts ---
    ctx_str = ""
    if isinstance(context, str):
        ctx_str = context

    elif isinstance(context, dict):
        # single dict
        ctx_str = context.get("page_content") or context.get("text", "")

    elif isinstance(context, list):
        parts = []
        for item in context:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("page_content") or item.get("text", ""))
            elif hasattr(item, "page_content"):
                parts.append(item.page_content)
        ctx_str = "\n\n".join(parts)

    # --- Safety check ---
    if not ctx_str.strip():
        return []

    # --- Optional trim if too long ---
    ctx_str = ctx_str.strip()
    if len(ctx_str) > MAX_CONTEXT_CHARS:
        ctx_str = ctx_str[:MAX_CONTEXT_CHARS]

    # --- LLM prompt ---
    prompt = dedent(f"""
    You are a flashcard content generator.
    Given the following extracted learning material, create exactly {num_cards} pairs of flashcards
    to help the student strengthen their knowledge of the key concepts.

    Rules:
    - Each flashcard must have:
        "front": a concise question or term (string), do not give any options here
        "back": the clear, correct answer/definition/explanation (string)
    - Do not include any extra commentary.
    - Do not frame questions directly based on the syllabus, or frame questions based on authors or books etc.
    - Output must be STRICT JSON array of objects with keys: "front", "back".

    Student info: {student_info}

    Context:
    \"\"\"{ctx_str}\"\"\"

    Generate exactly {num_cards} flashcards from the above context.
    """)

    # --- Run Ollama via stdin ---
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    proc = subprocess.Popen(
        ["ollama", "run", OLLAMA_MODEL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    stdout, stderr = proc.communicate(prompt)

    if stderr:
        print("LLM stderr (sanitized):", stderr[:500])

    # --- Repair and parse JSON ---
    json_str = repair_json_string(stdout)
    try:
        cards = json.loads(json_str)
    except json.JSONDecodeError:
        print("⚠️ LLM output was not valid JSON even after repairs.")
        return []

    return validate_flashcard_list(cards) or []