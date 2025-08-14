# utils/text_utils.py
from collections import Counter

def is_junk(text: str, min_len: int = 50, dup_thresh: float = 0.25) -> bool:
    """Detects junk text by length, repetition, and word diversity."""
    if not text.strip() or len(text) < min_len:
        return True
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    line_counts = Counter(lines)
    if line_counts and line_counts.most_common(1)[0][1] / len(lines) > dup_thresh:
        return True
    uniq_ratio = len(set(text.split())) / max(len(text.split()), 1)
    return uniq_ratio < 0.30