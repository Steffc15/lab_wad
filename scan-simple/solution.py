"""Completed version of student.py: every "TRY" hint done.

    python3 solution.py
"""

import re
from pathlib import Path

from PIL import ImageDraw
from rapidfuzz import fuzz

import common

ENLARGE = 2.0   # make the photo bigger before searching (small writing is found more easily)
PADDING = 0     # no margin: the rows are so close that a margin pulls in the neighbouring rows (6 -> 0: +30 points)
MIN_SIZE = 20   # boxes smaller than this (pixels) are dots or scribbles


# ---------- picture of each step ----------
def show(image, boxes, step):
    """Save outputs/<step>.png: the sheet with every box, and its label written on the right."""
    width, height = image.size
    picture = image.copy().crop((0, 0, width * 2, height))  # double width: right half is white
    picture.paste("white", (width, 0, width * 2, height))
    pen = ImageDraw.Draw(picture)
    for box in boxes:
        left, top, right, bottom = box["rect"]
        colour = box.get("colour", "blue")
        pen.rectangle(box["rect"], outline=colour, width=3)
        label = common.no_accents(box.get("label", ""))  # the built-in font has no ă, ț
        pen.text((width + left, top), label, fill=colour, font_size=24)
    Path("outputs").mkdir(exist_ok=True)
    picture.save(f"outputs/{step}.png")
    print(f"  picture: outputs/{step}.png")


# ---------- 1. FIND: where is the writing? ----------
def find(image):
    rects = common.find_text(image)

    # Remove tiny boxes: dots and scribbles.
    rects = [r for r in rects if r[2] - r[0] >= MIN_SIZE and r[3] - r[1] >= MIN_SIZE]

    boxes = [{"rect": rect} for rect in rects]
    show(image, boxes, "1_find")
    return boxes


# ---------- 2. READ: what does each box say? ----------
LOOKS_LIKE = str.maketrans({"0": "O", "1": "I", "5": "S", "8": "B"})


def fix_word(word):
    """A digit inside a word that is mostly letters is a misread letter: 'M1HNEA' -> 'MIHNEA'.
    Words that are mostly digits ('1241EB') are left alone."""
    letters = sum(c.isalpha() for c in word)
    digits = sum(c.isdigit() for c in word)
    return word.translate(LOOKS_LIKE) if letters > digits else word


def read(image, boxes):
    for box in boxes:
        piece = common.cut(image, box["rect"], PADDING)
        text, box["confidence"] = common.read_text(piece)
        text = re.sub(r"^\W*\d{1,2}\s*\)", "", text)  # drop the row number "4)" first: its digit is real
        box["text"] = " ".join(fix_word(w) for w in text.upper().split())
        box["label"] = f"{box['text']}  ({box['confidence']:.2f})"
        box["colour"] = "green" if box["confidence"] > 0.8 else "red"

    show(image, boxes, "2_read")
    return boxes


# ---------- 3. MATCH: which student is it? ----------
NOT_A_NAME = r"\b\d{3,4}[A-Z]{0,2}\b|\bERASMUS\b|\bOCT\b"  # group codes, "ERASMUS", the month


def without_initials(name):
    """'OMER H. Genan' -> 'OMER Genan': nobody writes their initials."""
    return " ".join(w for w in name.replace(".", " ").split() if len(w) > 1)


def name_similarity(text, name):
    """Normal similarity, or (a bit lower) one that ignores extra words on the line."""
    ignoring_extra = fuzz.token_set_ratio(common.plain(text), common.plain(name))
    return max(common.similarity(text, name), 0.9 * ignoring_extra)


def match(image, boxes, roster):
    # Similarity of every box with every student.
    pairs = []
    for i, box in enumerate(boxes):
        text = re.sub(NOT_A_NAME, " ", box["text"])
        for name in roster:
            pairs.append((name_similarity(text, without_initials(name)), i, name))

    # A student is on the sheet only once: give out the best pairs first, each name only once.
    chosen = {}
    used = set()
    for sim, i, name in sorted(pairs, reverse=True):
        if i not in chosen and name not in used and sim >= common.MAYBE:
            chosen[i] = (name, sim)
            used.add(name)

    matches = []
    for i, box in enumerate(boxes):
        name, sim = chosen.get(i, (None, 0))
        matches.append({"text": box["text"], "name": name, "similarity": sim})
        box["label"] = f"{name}  {sim:.0f}%" if name else "nobody"
        box["colour"] = "green" if sim >= common.SURE else "orange" if name else "red"

    show(image, boxes, "3_match")
    return matches


# ---------- run ----------
if __name__ == "__main__":
    image = common.enlarge(common.load_gray(), ENLARGE)
    roster = common.load_roster()
    boxes = find(image)
    boxes = read(image, boxes)
    matches = match(image, boxes, roster)
    common.score(matches, roster)
