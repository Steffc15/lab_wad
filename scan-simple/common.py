"""Helpers for student.py. You don't need to change this file."""

import csv
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from rapidfuzz import fuzz

HERE = Path(__file__).resolve().parent
logging.getLogger("RapidOCR").setLevel(logging.WARNING)  # hide the model's log lines


# ---------- input ----------

def load_gray() -> Image.Image:
    """test.jpeg, turned upright and grayscale."""
    image = ImageOps.exif_transpose(Image.open(HERE / "test.jpeg"))
    return image.convert("L").convert("RGB")  # gray, stored as 3 channels (what the model expects)


def load_roster() -> list[str]:
    """The 21 student names from roster.csv, like 'OMER H. Genan'."""
    with open(HERE / "roster.csv", newline="", encoding="utf-8") as f:
        return [f"{row['last_name']} {row['first_name']}" for row in csv.DictReader(f)]


def enlarge(image: Image.Image, factor: float) -> Image.Image:
    return image.resize((round(image.width * factor), round(image.height * factor)), Image.LANCZOS)


def cut(image: Image.Image, rect, padding: int) -> Image.Image:
    """Cut a rectangle (left, top, right, bottom) out of the image, with a margin around it."""
    left, top, right, bottom = rect
    return image.crop((max(0, left - padding), max(0, top - padding),
                       min(image.width, right + padding), min(image.height, bottom + padding)))


# ---------- the OCR model (RapidOCR, small neural networks) ----------

@lru_cache(maxsize=1)
def _model():
    from rapidocr import RapidOCR
    return RapidOCR()


def find_text(image: Image.Image) -> list[tuple[float, float, float, float]]:
    """Rectangles (left, top, right, bottom) around every piece of writing."""
    result = _model()(np.array(image), use_det=True, use_cls=False, use_rec=False)
    if result.boxes is None:
        return []
    return [(float(b[:, 0].min()), float(b[:, 1].min()), float(b[:, 0].max()), float(b[:, 1].max()))
            for b in result.boxes]


def read_text(image: Image.Image) -> tuple[str, float]:
    """Read one piece of writing. Returns (text, confidence from 0 to 1)."""
    result = _model()(np.array(image), use_det=False, use_cls=False, use_rec=True)
    if not result.txts:
        return "", 0.0
    return result.txts[0].strip(), float(result.scores[0])


# ---------- comparing text ----------

def no_accents(text: str) -> str:
    """'Vlăduț' -> 'Vladut'."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def plain(text: str) -> str:
    """'Vlăduț-Andrei' -> 'vladut andrei': lowercase, no accents, no punctuation."""
    return re.sub(r"[^a-z0-9]+", " ", no_accents(text).casefold()).strip()


def similarity(a: str, b: str) -> float:
    """How alike two texts are, from 0 to 100, ignoring word order and accents."""
    return fuzz.token_sort_ratio(plain(a), plain(b))


# ---------- scoring ----------

SURE = 80    # similarity >= 80: the name was found       -> 10 points
MAYBE = 60   # similarity 60-80: probably the name         ->  5 points
             # the same student given to two texts         -> -5 points


def score(matches: list[dict], roster: list[str]) -> int:
    """matches: [{"text": what was read, "name": a roster name or None, "similarity": 0-100}, ...]
    Prints a table and returns the total points."""
    best: dict[str, float] = {}
    times: dict[str, int] = {}
    for m in matches:
        if m["name"] and m["similarity"] >= MAYBE:
            best[m["name"]] = max(best.get(m["name"], 0), m["similarity"])
            times[m["name"]] = times.get(m["name"], 0) + 1

    print("\n  points  similarity  student")
    total = 0
    for name in roster:
        sim = best.get(name, 0)
        points = 10 if sim >= SURE else 5 if sim >= MAYBE else 0
        note = ""
        if times.get(name, 0) > 1:
            points -= 5 * (times[name] - 1)
            note = f"  (found {times[name]} times: -5 each extra)"
        total += points
        print(f"  {points:6}  {f'{int(sim)}%' if sim else '-':>10}  {name}{note}")

    print(f"\n  SCORE: {total} points\n")
    return total
