# CGV Signature Tracker — System Architecture

**Module:** CS402.3 Computer Graphics and Visualization
**Coursework:** Student Attendance Management System (SAMS) based on signing sheets
**Module Leader:** Dr. Rasika Ranaweera
**Type:** Group Assignment (10 members)

---

## 1. Purpose & Scope

A **Student Attendance Management System (SAMS)** that reads photographed signing
sheets, decides who was **present** or **absent** from the appearance of a signature,
stores results in a local database, and visualizes attendance per student.

The system is delivered as **three command-line programs**, exactly as required by the
brief:

| Program | Invocation | Responsibility |
|---------|-----------|----------------|
| `sams.py` | `python sams.py 10.07.2019.png info.xml` | Image processing → signature detection → store attendance in DB. **Shows each processing step.** |
| `infovis.py` | `python infovis.py 001` | Read DB → render attendance summary graph for one student. |
| `investigate.py` | `python investigate.py 001` | Signature **recognition**: compare a student's signatures across sheets/reference and report mismatches (bonus marks). |

> **Note on the two data models.** The PDF's illustrative table uses `# | Index | Name |
> Signature`. The **actual** signing sheets (the 5 images in `CGV Signing Sheets.zip`)
> use `No | Student No | Title | Student Name | Signature` with 8-digit student numbers
> (`10000409`, `10009301`–`10009306`) and **6 students per sheet**. The architecture
> targets the **real** sheet layout, while `info.xml` follows the structure in Figure 1
> of the brief.

---

## 2. High-Level Architecture

The system follows a **layered pipeline** architecture with a shared persistence layer.
Each layer is independently testable — which maps cleanly onto a 10-person team.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLI ENTRY POINTS                              │
│   sams.py            infovis.py             investigate.py                 │
└─────────┬───────────────────┬───────────────────────┬─────────────────────┘
          │                   │                        │
          ▼                   ▼                        ▼
┌──────────────────┐  ┌────────────────┐   ┌──────────────────────────┐
│  ATTENDANCE      │  │ VISUALIZATION  │   │  RECOGNITION             │
│  ORCHESTRATOR    │  │ SERVICE        │   │  SERVICE                 │
│ (pipeline driver)│  │ (charts)       │   │ (signature matching)     │
└───┬──────────────┘  └───────┬────────┘   └──────────┬───────────────┘
    │                         │                       │
    ▼                         │                       │
┌────────────────────────┐    │                       │
│  IMAGE PROCESSING       │   │                       │
│  PIPELINE               │   │                       │
│  1. Load & preprocess   │   │                       │
│  2. Greyscale           │   │                       │
│  3. Denoise             │   │                       │
│  4. Deskew / perspective│   │                       │
│  5. Binarize (adaptive) │   │                       │
│  6. Table-line detection│   │                       │
│  7. Cell extraction     │   │                       │
│  8. Ink-density → P/A   │   │                       │
└───┬────────────────────┘    │                       │
    │                         │                       │
    ▼                         ▼                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          DOMAIN / DATA LAYER                              │
│  Roster (info.xml parser)   ·   Models (Student, Sheet, Attendance)      │
│  Repository (DB access)     ·   SQLite database (attendance.db)          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │  ARTIFACTS (on disk)         │
                    │  • attendance.db (SQLite)    │
                    │  • output/steps/*.png        │
                    │    (greyscale, binary, grid…)│
                    │  • output/charts/*.png       │
                    │  • output/reports/*.txt      │
                    └──────────────────────────────┘
```

### Design principles
- **Separation of concerns** — image processing never touches the DB directly; it emits a
  data structure the domain layer persists.
- **OOP throughout** — each pipeline stage is a class implementing a common interface
  (assessment criterion: *OOP concepts*).
- **Every stage is observable** — stages save their output image so the report can show
  greyscale → binary → grid → cells (assessment criterion: *screenshots of the entire
  step-by-step process*).
- **Configuration over hard-coding** — thresholds, paths, and expected row counts live in
  `config.py`, not scattered through the code.

---

## 3. The Image Processing Pipeline (heart of the system)

`sams.py` runs an ordered chain of **processing stages**. Every stage takes an image (and
context) and returns a transformed image, while **writing a snapshot to `output/steps/`**
so progress is visible both on screen and for the report.

### Stage sequence

| # | Stage | Technique / OpenCV calls | Why it's needed | Snapshot |
|---|-------|--------------------------|-----------------|----------|
| 1 | **Load** | `cv2.imread`, resize to working width | Normalize huge phone photos (3024×4032) to a manageable size | `01_original.png` |
| 2 | **Greyscale** | `cv2.cvtColor(BGR2GRAY)` | Colour is irrelevant for ink detection; simplifies later steps | `02_grey.png` |
| 3 | **Denoise / blur** | `cv2.GaussianBlur` or `fastNlMeansDenoising` | Phone photos have sensor noise + paper texture | `03_denoised.png` |
| 4 | **Deskew / perspective** | Edge detect → largest quadrilateral contour → `cv2.getPerspectiveTransform` + `warpPerspective`; fallback `minAreaRect` rotation | Sheets are photographed at an angle/rotation — must be flattened before the grid is reliable | `04_deskewed.png` |
| 5 | **Binarize** | `cv2.adaptiveThreshold` (Gaussian, inverted) | Uneven lighting/shadows make a global threshold fail; adaptive handles it. Ink → white on black | `05_binary.png` |
| 6 | **Table-line detection** | Morphology with long horizontal & vertical kernels (`getStructuringElement` + `morphologyEx OPEN`), combine masks | Isolate the printed table grid to locate cells without hard-coded coordinates | `06a_h_lines.png`, `06b_v_lines.png`, `06c_grid.png` |
| 7 | **Cell extraction** | Find grid intersections / `findContours` on grid cells → sort into rows & columns → crop the **Signature** column for each of the 6 rows | Produce one image per student's signature box | `07_cells_overlay.png`, `07_row_<n>.png` |
| 8 | **Presence decision** | For each signature crop: count ink pixels; `present = ink_ratio > THRESHOLD` | Turns pixels into the present/absent verdict | `08_result_overlay.png` |

### Stage interface (OOP contract)

```python
class ProcessingStage(ABC):
    name: str
    @abstractmethod
    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray: ...
    def snapshot(self, image, ctx): ...   # saves to output/steps/ + optional live show
```

Concrete stages: `LoadStage`, `GreyscaleStage`, `DenoiseStage`, `DeskewStage`,
`BinarizeStage`, `TableLineStage`, `CellExtractionStage`, `PresenceDecisionStage`.
The `Pipeline` class holds an ordered list and runs them, threading a `PipelineContext`
(holds the roster, detected cells, per-row verdicts, output dirs) through the chain.

---

## 4. Presence Decision & Recognition

### Presence (core — all students)
After Stage 7 each signature cell is a small binary crop. The `PresenceDecisionStage`
computes:

```
ink_ratio = (# ink pixels) / (cell width × cell height)
present   = ink_ratio > PRESENCE_THRESHOLD    # tuned on the 5 given sheets
```

Guard against noise: ignore specks via a minimum connected-component area so a stray dot
doesn't count as a signature.

### Recognition (bonus — `investigate.py`)
For students who have **reference signatures** collected, compare the detected signature
against references and flag non-matches (possible wrong-person/forgery):

- **Feature matching:** ORB/SIFT keypoints + descriptor matching (`cv2.ORB_create`,
  `BFMatcher`), ratio of good matches → similarity score.
- **Structural similarity:** `skimage.metrics.structural_similarity (SSIM)` on
  size-normalized crops as a second opinion.
- **Verdict:** `match = score > MATCH_THRESHOLD`; report per sheet whether the signature
  is consistent with the student's reference set.

Reference signatures live in `data/reference_signatures/<student_no>/*.png`.

---

## 5. Domain & Data Layer

### `info.xml` (input roster)
Follows the brief's Figure 1 structure, adapted to the real 8-digit indices and the extra
`title` field:

```xml
<?xml version="1.0"?>
<nsbm>
  <students>
    <batches>
      <batch id="2016.1">
        <subject code="CS402.3">Computer Graphics and Visualization</subject>
        <student>
          <index>10000409</index>
          <title>Ms</title>
          <name>M S Dilshanika Perera</name>
        </student>
        <student>
          <index>10009301</index>
          <title>Mr</title>
          <name>C W M A Shehan Abeyrathne</name>
        </student>
        <!-- 10009302 … 10009306 -->
      </batch>
    </batches>
  </students>
</nsbm>
```

`RosterParser` reads this into `Student` objects. The **row order in the roster** maps to
the **row order of extracted cells** (both are sorted top-to-bottom), which is how a
detected signature is attributed to a student.

### Data models
```python
@dataclass
class Student:      index: str; title: str; name: str
@dataclass
class Sheet:        filename: str; date: date; hall: str | None
@dataclass
class Attendance:   student_index: str; sheet_date: date; present: bool; ink_ratio: float
```

### Database — SQLite (`attendance.db`)
Chosen because it is **local, zero-config, file-based**, exactly matching "store the
attendance in a local DB."

```sql
CREATE TABLE student (
    index_no TEXT PRIMARY KEY,
    title    TEXT,
    name     TEXT
);
CREATE TABLE sheet (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    date     TEXT,                    -- ISO yyyy-mm-dd
    hall     TEXT,
    UNIQUE(date)
);
CREATE TABLE attendance (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_no TEXT REFERENCES student(index_no),
    sheet_id   INTEGER REFERENCES sheet(id),
    present    INTEGER,              -- 0/1
    ink_ratio  REAL,
    UNIQUE(student_no, sheet_id)     -- re-running a sheet updates, not duplicates
);
```

`AttendanceRepository` wraps all SQL (insert student, upsert sheet, upsert attendance,
query attendance-by-student for the visualizer). No other layer writes SQL.

---

## 6. Visualization (`infovis.py`)

Reads attendance for one student across all processed sheets and renders a graph with
**matplotlib**.

- **Primary chart:** a per-date **present/absent timeline** (bar or step plot) for the
  student — dates on X, present(1)/absent(0) on Y.
- **Summary:** attendance **percentage** as a headline number + a small pie/donut
  (present vs absent count).
- Saves to `output/charts/<student_no>.png` and shows it on screen.

> Follows the brief: *"show a summary of attendance for a given student … using a suitable
> graph."*

---

## 7. Module / File Structure

```
CGV-Signature-Tracker/
├── sams.py                     # entry: image processing → DB
├── infovis.py                  # entry: visualization
├── investigate.py              # entry: signature recognition (bonus)
├── requirements.txt
├── config.py                   # thresholds, paths, expected rows/cols
│
├── sams/                       # main package
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── base.py             # ProcessingStage ABC, PipelineContext, Pipeline
│   │   ├── load.py
│   │   ├── greyscale.py
│   │   ├── denoise.py
│   │   ├── deskew.py
│   │   ├── binarize.py
│   │   ├── table_lines.py
│   │   ├── cells.py            # cell extraction
│   │   └── presence.py         # ink-density decision
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py           # Student, Sheet, Attendance
│   │   └── roster.py           # info.xml parser
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py         # connection + schema bootstrap
│   │   └── repository.py       # AttendanceRepository
│   │
│   ├── recognition/
│   │   ├── __init__.py
│   │   └── matcher.py          # ORB/SSIM signature comparison
│   │
│   ├── viz/
│   │   ├── __init__.py
│   │   └── charts.py           # matplotlib summary charts
│   │
│   └── util/
│       ├── __init__.py
│       ├── imaging.py          # shared cv2 helpers, snapshot saver
│       └── logging.py          # progress/console output
│
├── data/
│   ├── sheets/                 # the 5 input images
│   ├── info.xml
│   └── reference_signatures/   # <student_no>/*.png for recognition
│
├── output/
│   ├── steps/                  # per-stage snapshots (for the report)
│   ├── charts/
│   └── reports/
│
├── tests/                      # pytest: pipeline stages, roster, repo
│   ├── test_roster.py
│   ├── test_repository.py
│   ├── test_presence.py
│   └── test_pipeline.py
│
└── docs/
    ├── ARCHITECTURE.md         # this file
    └── ROLES.md                # 10-member role split
```

---

## 8. Technology Stack

| Concern | Library | Reason |
|---------|---------|--------|
| Image processing | **OpenCV (`opencv-python`)** | Industry-standard CV: threshold, morphology, contours, perspective warp |
| Numerics | **NumPy** | Array ops backing all pixel math |
| Recognition | **OpenCV (ORB/SIFT)** + **scikit-image (SSIM)** | Keypoint matching + structural similarity |
| Visualization | **Matplotlib** | "Suitable graph" for attendance summary |
| Database | **SQLite** (`sqlite3`, stdlib) | Local, zero-config DB as required |
| XML parsing | `xml.etree.ElementTree` (stdlib) | Parse `info.xml` |
| CLI | `argparse` (stdlib) | Clean `python sams.py <img> <xml>` interface |
| Testing | **pytest** | Unit tests → "testing results" marks |

`requirements.txt`: `opencv-python`, `numpy`, `matplotlib`, `scikit-image`, `pytest`.

---

## 9. Execution Flows

### `sams.py 10.07.2019.png info.xml`
```
1. Parse args (image path, xml path)
2. RosterParser.parse(info.xml)              → [Student]
3. DB.bootstrap(); Repository.upsert_students(roster)
4. Pipeline([Load, Greyscale, Denoise, Deskew,
             Binarize, TableLines, Cells, Presence])
     .run(image, ctx)                         → each stage saves a snapshot + prints step
5. ctx.verdicts (row → present/ink_ratio) zipped with roster order
6. Repository.upsert_sheet(date from filename/sheet)
   Repository.upsert_attendance(per student)
7. Print summary table: index | name | PRESENT/ABSENT
```

### `infovis.py 001`
```
1. Repository.attendance_for(student_no)      → rows across sheets
2. charts.render_summary(student, rows)       → timeline + % + donut
3. Save output/charts/<no>.png + show
```

### `investigate.py 001`
```
1. Load reference signatures for student
2. For each processed sheet, extract that student's signature crop
3. matcher.compare(reference, detected)       → score + match?
4. Print report: sheet date | score | MATCH / MISMATCH
```

---

## 10. Mapping to Assessment Criteria

| Criterion (from brief) | Where it's satisfied |
|------------------------|----------------------|
| Quality / coding styles / **OOP** | Stage classes, repository pattern, dataclasses, package layout |
| **Executable program** | 3 CLI entry points with `argparse` |
| Use of **image-processing libraries** | OpenCV, NumPy, scikit-image |
| Use of **image-processing techniques** | greyscale, denoise, deskew/perspective, adaptive binarize, morphology line-detection, contours |
| **Screenshots of the entire step-by-step process** | every stage writes to `output/steps/` |
| **Testing results** | pytest suite in `tests/` run over all 5 sheets |
| **Recognition** (higher grades) | `investigate.py` + `recognition/matcher.py` |
| Data **visualization** | `infovis.py` + matplotlib charts |

---

## 11. Build Order (recommended)

1. **Skeleton + config + models + roster parser** (unblocks everyone).
2. **DB layer** (schema, repository) — mockable, lets viz/recognition proceed in parallel.
3. **Pipeline stages 1–5** (load → binarize) — visible progress fast.
4. **Stages 6–7** (line detection → cell extraction) — the hard CV; iterate on the 5 sheets.
5. **Stage 8** (presence) + wire `sams.py` end-to-end → DB.
6. **`infovis.py`** once DB has rows.
7. **`investigate.py`** recognition (bonus) last.
8. **Tests + report screenshots** throughout.

See `docs/ROLES.md` for the 10-member split.
