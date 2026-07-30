# CGV Signature Tracker — Member Package

**Member:** WDJI Senarathna (29015)
**Role:** Recognition & QA Engineer
**GitHub:** Janakaishansenarathna
**Your branch:** `feature/janaka-recognition`

Welcome! This package contains **only the files you own** (Section 3) plus this guide.
These files will **not run on their own** — they import the rest of the project. To run
and test them, drop them into the shared team repository (Section 2). You edit only
these files; everyone else edits theirs; git merges cleanly because nobody overlaps.

---

## 1. System architecture in 60 seconds

Three command-line programs on top of a layered, object-oriented core:

| Program | Command | Does |
|---------|---------|------|
| `sams.py` | `python sams.py data/sheets/2019-06-28.jpeg data/info.xml` | 8-stage image pipeline -> present/absent -> SQLite |
| `infovis.py` | `python infovis.py 10009301` | attendance chart for one student |
| `investigate.py` | `python investigate.py 10009301` | signature recognition vs reference library |

The pipeline stages (each one a class, each saves a snapshot to `output/steps/`):
**Load -> Greyscale -> Denoise -> Deskew -> Binarize -> Table-lines -> Cell-extraction -> Presence.**
Layers: `sams/pipeline/` (image processing), `sams/domain/` (models + roster),
`sams/data/` (SQLite), `sams/recognition/`, `sams/viz/`, `sams/util/`.

Full design: **docs/ARCHITECTURE.md**. Team/ownership map: **docs/ROLES.md**.

## 2. Setup — dropping your files into the shared repo

Your zip has only your files, so run them from inside the full team repo:

```bash
# 1. clone the shared team repository (ask WKR Pinsiri / the lead for the URL)
git clone <team-repo-url> CGV-Signature-Tracker
cd CGV-Signature-Tracker
python -m pip install -r requirements.txt

# 2. make your branch, then copy YOUR files from this zip over the repo copies
git checkout -b feature/janaka-recognition
#    (copy the files under Section 3 into the same paths in the repo)

# 3. now you can run and test the whole project:
python sams.py data/sheets/2019-06-28.jpeg data/info.xml
python -m pytest -q      # all 35 tests should pass
```

## 3. YOUR files (strict ownership — edit only these)

- `sams/recognition/matcher.py — shape-template NCC matcher (+SSIM/ORB)`
- `investigate.py — recognition CLI`
- `collect_references.py — reference-library builder`
- `tests/ — the whole pytest suite (35 tests)`

These are the exact files in this zip. **Only ever commit these paths.** If you need a
change in someone else's file, ask that file's owner (see docs/ROLES.md).

## 4. YOUR tasks (real work, roughly in priority order)

1. Sweep MATCH_THRESHOLD (0.18–0.30) with a leave-one-out protocol and chart genuine-vs-impostor score distributions; justify the chosen value.
2. Make investigate.py also write its report to output/reports/<index>.txt.
3. Add matcher tests for rotated/scaled versions of the same synthetic signature.
4. Keep the whole suite green as teammates merge; add regression tests when anyone's change breaks something.

Also search your files for `TODO(owner)` markers — those are yours.

## 5. Git workflow (on YOUR computer)

```bash
# inside the cloned repo, on your branch (Section 2):
git config user.name "Janakaishansenarathna"
git config user.email "janakasenarathna2001@gmail.com"

# work, committing small and often AS YOU GO — stage ONLY your own files:
git add <only your files, e.g. the paths in Section 3>
git commit -m "one line describing what you just changed (WDJI Senarathna 29015)"
git push -u origin feature/janaka-recognition
```

When a task is done, open a Pull Request from `feature/janaka-recognition` into `main`. Because every
member touches a different set of files, the lead can merge all seven branches with no
conflicts. Small, real commits made while you work are exactly what the module leader
wants to see — never commit files that are not yours.

## 6. Your report section (minimum 2 pages, in your own words)

The group report is `report/CS402.3_CGV_Report.docx` (kept in the shared repo).
Your section should explain, with your own figures and words: the shape-template + NCC method and why ORB fails on sparse crops, the reference-collection workflow, the impostor-detection result, and the honest leave-one-out analysis of the absent-mark limitation (Section 9.5 of the report).

Use the step images your code produces in `output/steps/` as your figures. Two pages
minimum — code snippets and illustrations count, but the explanation must be yours.
