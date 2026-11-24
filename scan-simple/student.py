"""Read a handwritten attendance sheet and find the students on it.

    python3 student.py

    test.jpeg -> 1. FIND   -> 2. READ   -> 3. MATCH          -> SCORE
                 where is     what does    which student
                 writing?     it say?      (roster.csv) is it?

Everything already works, in a simple way. Your job: raise the SCORE.
Change one thing, run again, look at the pictures in outputs/. Hints: "TRY".
"""

import re
from pathlib import Path

from PIL import ImageDraw

import common

ENLARGE = 2.0   # make the photo bigger before searching (small writing is found more easily)
PADDING = 0     # no margin: rows are close together, a margin pulls in the neighbouring rows (6 -> 0: 120 -> 135)
MIN_SIZE = 20   # boxes smaller than this (pixels) are dots or scribbles, not writing


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

    # Remove tiny boxes (dots, scribbles): too narrow or too short to be a name.
    rects = [r for r in rects if r[2] - r[0] >= MIN_SIZE and r[3] - r[1] >= MIN_SIZE]

    boxes = [{"rect": rect} for rect in rects]
    show(image, boxes, "1_find")
    return boxes


# ---------- 2. READ: what does each box say? ----------
LOOKS_LIKE = str.maketrans({"0": "O", "1": "I", "5": "S", "8": "B"})


def fix_word(word):
    """A digit inside a mostly-letter word is a misread letter: 'M1HNEA' -> 'MIHNEA'.
    Mostly-digit words like the group code '1241EB' are left alone."""
    letters = sum(c.isalpha() for c in word)
    digits = sum(c.isdigit() for c in word)
    return word.translate(LOOKS_LIKE) if letters > digits else word


def read(image, boxes):
    for box in boxes:
        piece = common.cut(image, box["rect"], PADDING)
        text, box["confidence"] = common.read_text(piece)
        text = re.sub(r"^\W*\d{1,2}\s*[).]", "", text)  # drop the row number "4)" first: its digit is real
        # Names are written in CAPITALS; then fix digits that are really letters.
        box["text"] = " ".join(fix_word(w) for w in text.upper().split())
        box["label"] = f"{box['text']}  ({box['confidence']:.2f})"
        box["colour"] = "green" if box["confidence"] > 0.8 else "red"

    show(image, boxes, "2_read")
    return boxes


# ---------- 3. MATCH: which student is it? ----------
NOT_A_NAME = r"\b\d{3,4}[A-Z]{0,2}\b|\bERASMUS\b|\bOCT\b"  # group codes, "ERASMUS", the month


def without_initials(name):
    """'OMER H. Genan' -> 'OMER Genan': nobody writes their initials on the sheet."""
    return " ".join(w for w in name.replace(".", " ").split() if len(w) > 1)


def match(image, boxes, roster):
    matches = []
    for box in boxes:
        text = re.sub(NOT_A_NAME, " ", box["text"])
        best_name, best_sim = None, 0
        for name in roster:
            sim = common.similarity(text, without_initials(name))
            if sim > best_sim:
                best_name, best_sim = name, sim
        matches.append({"text": box["text"], "name": best_name, "similarity": best_sim})
        box["label"] = f"{best_name}  {best_sim:.0f}%"
        box["colour"] = "green" if best_sim >= common.SURE else "orange" if best_sim >= common.MAYBE else "red"

    # TRY: remove what is not a name before comparing: "4)", group codes "1241EB", "ERASMUS"
    # TRY: roster names have initials ("OMER H. Genan") nobody writes -> leave them out
    # TRY: one student can only be on the sheet once -> don't give the same name to two boxes

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
