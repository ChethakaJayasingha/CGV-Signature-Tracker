# CGV Signature Tracker

**Student Attendance Management System (SAMS)** based on signing sheets.
CS402.3 — Computer Graphics and Visualization · Module Leader: Dr. Rasika Ranaweera.

Reads photographed signing sheets, decides who was **present / absent** from the
appearance of a signature, stores the result in a local database, visualizes a
student's attendance, and (bonus) verifies signatures via recognition.

---

## The three programs

```bash
# 1. Process a sheet: image pipeline -> detect signatures -> store in DB.
#    Shows each processing step and saves step images for the report.
python sams.py data/sheets/12.07.2019.png data/info.xml

# 2. Visualize one student's attendance (%, donut, timeline).
python infovis.py 10000409          # or a short index like: python infovis.py 409

# 3. Recognition (bonus): build a reference library, then verify signatures.
python collect_references.py         # crops genuine signatures from present cells
python investigate.py 10000409       # compares each sheet's signature to references
```

---

## Setup

```bash
python -m pip install -r requirements.txt
```

Then place the five signing-sheet images from `CGV Signing Sheets.zip` into
`data/sheets/` (see `data/sheets/README.md` for naming), and process each:

```bash
python sams.py data/sheets/12.07.2019.png data/info.xml
python sams.py data/sheets/05.07.2019.png data/info.xml
# ... all five, then:
python infovis.py 10000409
```

## Running the tests

```bash
python -m pytest -q
```

---

## The image-processing pipeline

`sams.py` runs 8 observable stages; each saves a snapshot to `output/steps/`
(perfect for the report):

| # | Stage | Technique | Snapshot |
|---|-------|-----------|----------|
| 1 | Load | resize phone photo | `01_original.png` |
| 2 | Greyscale | BGR → GRAY | `02_grey.png` |
| 3 | Denoise | Gaussian blur | `03_denoised.png` |
| 4 | Deskew | perspective transform | `04_deskewed.png` |
| 5 | Binarize | adaptive threshold (inverted) | `05_binary.png` |
| 6 | Table lines | morphology (H/V line masks) | `06_grid_*.png` |
| 7 | Cell extraction | contours → signature column, per row | `07_cells_overlay.png` |
| 8 | Presence | ink-density threshold | `08_result_overlay.png` |

---

## Project layout

```
sams.py, infovis.py, investigate.py   # the three CLI programs
config.py                             # thresholds & paths (tune here)
sams/                                 # package
  pipeline/   (8 stages + driver)     # image processing
  domain/     (models, info.xml)      # roster
  data/       (SQLite + repository)    # local DB
  recognition/(ORB + SSIM matcher)    # signature verification
  viz/        (matplotlib charts)     # visualization
  util/       (imaging, dates, log)   # shared helpers
data/  sheets/ · info.xml · reference_signatures/
output/ steps/ · charts/ · reports/   # generated (git-ignored)
tests/                                # pytest suite
docs/  ARCHITECTURE.md · ROLES.md
```


---

## Tech stack

OpenCV · NumPy · scikit-image (recognition) · Matplotlib (visualization) ·
SQLite (local DB) · pytest.

