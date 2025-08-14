import os
import subprocess
import json
import re
from textwrap import dedent
from config import OLLAMA_MODEL

MAX_CONTEXT_CHARS = 12000  # safety guard; adjust as needed


def repair_json_string(bad_json: str) -> str:
    """
    Try to repair common LLM JSON errors:
    - Remove duplicate/trailing commas
    - Fix unmatched braces/brackets
    - Remove text before/after JSON block
    """
    # Extract the biggest JSON array found in output
    match = re.search(r"\[.*\]", bad_json, re.DOTALL)
    if match:
        json_part = match.group(0)
    else:
        json_part = bad_json

    # Remove control characters (e.g., from OCR noise)
    json_part = re.sub(r"[\x00-\x1F\x7F]", " ", json_part)

    # Remove duplicate commas
    json_part = re.sub(r",\s*(\]|\})", r"\1", json_part)

    return json_part.strip()


def validate_mcq_list(mcqs):
    """
    Ensure each MCQ dict has required keys and correct formats.
    Remove invalid ones, fix easy issues, and return cleaned list.
    """
    cleaned = []
    seen_questions = set()

    for mcq in mcqs:
        if not isinstance(mcq, dict):
            continue
        if "question" not in mcq or "options" not in mcq or "correct_option" not in mcq:
            continue
        if not isinstance(mcq["options"], list) or len(mcq["options"]) != 4:
            continue
        if mcq["correct_option"] not in ["A", "B", "C", "D"]:
            continue
        q_text = mcq["question"].strip()
        if q_text in seen_questions:
            continue
        seen_questions.add(q_text)
        cleaned.append({
            "question": q_text,
            "options": mcq["options"],
            "correct_option": mcq["correct_option"]
        })

    return cleaned


def generate_mcqs(student_info: dict, context: str):
    if not context or not context.strip():
        return []

    # Optional: trim very long contexts
    ctx = context.strip()
    if len(ctx) > MAX_CONTEXT_CHARS:
        ctx = ctx[:MAX_CONTEXT_CHARS]

    prompt = dedent(f"""
    You are a question paper generator.
    Given the following extracted exam content, create original MCQs based solely on the concepts in the text.

    Rules:
    - Generate ONLY new MCQs, do not answer them.
    - Avoid copying exact wording from the text; rephrase concepts.
    - Each MCQ must have 4 options: A, B, C, D.
    - Randomize the position of the correct answer.
    - Provide the correct answer key separately.
    - Output format must be STRICT JSON array of objects with keys:
      "question" (string),
      "options" (array of 4 strings),
      "correct_option" ("A","B","C","D")


    Student info: {student_info}

    Context:
    \"\"\"{ctx}\"\"\"

    Generate exactly 10 MCQs from the above context.
    """)

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

    # Attempt to parse JSON
    json_str = repair_json_string(stdout)
    try:
        mcqs = json.loads(json_str)
    except json.JSONDecodeError:
        print("⚠️ LLM output was not valid JSON even after repairs.")
        return []

    # Validate and clean the MCQs
    valid_mcqs = validate_mcq_list(mcqs)
    return valid_mcqs
