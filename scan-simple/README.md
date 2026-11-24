# Read the attendance sheet

```bash
pip install -r requirements.txt
python3 student.py
```

```
test.jpeg -> 1. FIND -> 2. READ -> 3. MATCH -> SCORE
             where is    what does  which student
             writing?    it say?    (roster.csv)?
```

**Your goal: raise the SCORE.** Points for every student found on the sheet:

- **10 points:** the name was read with similarity of 80% or more
- **5 points:** similarity between 60% and 80%
- **−5 points:** for every extra time the same student is found

How to work:

1. Look at the pictures in `outputs/` (`1_find.png`, `2_read.png`, `3_match.png`). Which step went wrong?
2. Change **one** thing in `student.py`. The `TRY` comments give ideas.
3. Run it again and compare the score.

| File | |
|---|---|
| `student.py` | **Your code.** |
| `common.py` | Helpers and the scoring. No need to change it. |
| `solution.py` | One finished version. Don't peek before you try! |
| `test.jpeg` | The photo of the sheet. |
| `roster.csv` | The class list. Columns: `id,first_name,last_name,group` (only the names are used). |

To use a new sheet, replace `test.jpeg` with your photo (same name) and `roster.csv` with your class list.
