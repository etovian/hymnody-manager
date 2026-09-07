# GEMINI.md — Hymnody Manager & Worship Planner

## Project Overview

**Hymnody Manager** is a local Python web application designed for Lutheran worship planning, hymnody indexing, sanctuary audio streaming, and mobile playlist export. It scans `.m4a` accompaniment audio files (specifically *The Concordia Organist* set discs 1–31 and Divine Service 1–5 settings), stores metadata in a local SQLite database (`hymnody.db`), and provides a dual-mode browser interface (Desktop Planner & Sanctuary Mobile Mode).

- **GitHub Repository**: [https://github.com/etovian/hymnody-manager](https://github.com/etovian/hymnody-manager)

---

## Key Features & System Architecture

1. **Read-Only Metadata Indexing & Deduplication**:
   - Custom binary MP4 atom parser (`src/scanner.py`) extracts titles, hymn numbers, disc/track numbers, album, artist, year, and liturgical seasons without modifying source audio files.
   - Automatic track deduplication and incremental ingestion handling suffixed duplicate files (e.g. `101_Hymn (1).m4a`), backed by a standalone cleanup maintenance script (`scripts/cleanup_duplicates.py`).

2. **Divine Service & Daily Office Presets + Custom Template Editor**:
   - Pre-configured templates for **Divine Service 1–5 (DS1–DS5)**, **Matins**, and **Vespers** that automatically insert liturgical ordinaries (*Kyrie*, *Gloria*, *Sanctus*, *Agnus Dei*, *Nunc Dimittis*) alongside hymn slots.
   - Dual-tab Worship Planner sidebar (Liturgical Ordinaries vs Hymnody Catalog) with drag-and-drop custom template builder and alphabetized template selection.

3. **Liturgical Rubric Validation & Missing Audio Alerts**:
   - Built-in rubric validator (`src/services.py`) verifying liturgical completeness (e.g., proper canticle placement, missing ordinaries).
   - Real-time UI indicator badges and export warnings for missing audio tracks.

4. **HTTP 206 Audio Streaming & Single-Track Mode**:
   - FastAPI streaming endpoint supporting range requests for instant browser seeking and track jumping.
   - Interactive preview play buttons in the Hymnal catalog and customizable auto-advance / single-track playback settings.

5. **Mobile Package Exporter**:
   - Downloads a `.zip` file with dynamically named audio tracks (e.g., `01_Invocation_Hymn_331.m4a`, `02_DS2_Kyrie.m4a`) based on liturgical day, date, or preset name, accompanied by a `playlist.m3u` file for seamless mobile Bluetooth playback.

6. **Sanctuary Mobile UI**:
   - High-contrast touch view with oversized **PLAY**, **PAUSE**, and **NEXT TRACK** controls designed for non-technical church volunteers.

---

## Directory Structure

```
c:\dev\IdeaProjects\hymnody-manager\
├── music\                  # Audio files (.m4a) — READ-ONLY! Git Ignored!
├── docs\
│   └── plans\              # Design specs, implementation plans, and hymn reports
│       ├── 2026-08-30-hymnody-manager-design-spec.md
│       ├── 2026-09-01-worship-planning-features-design.md
│       ├── 2026-09-03-liturgical-and-hymn-catalog-tabs-design.md
│       ├── 2026-09-05-tabbed-template-editor-design.md
│       ├── 2026-09-06-track-deduplication-design.md
│       └── ...
├── scripts\
│   └── cleanup_duplicates.py # Maintenance script to purge duplicate suffixed audio files
├── src\
│   ├── scanner.py          # MP4 atom metadata parser, directory scanner & deduplication
│   ├── database.py         # SQLite schema initialization, migrations & CRUD repository
│   ├── services.py         # Presets, template builder & liturgical rubric validator
│   ├── exporter.py         # Mobile zip package & m3u generator with dynamic naming
│   ├── main.py             # FastAPI REST endpoints & HTTP 206 range streamer
│   └── static\             # Frontend web assets (index.html, styles.css, app.js)
├── tests\                  # Automated pytest test suite (58 passing tests)
│   ├── test_api.py
│   ├── test_cleanup_duplicates.py
│   ├── test_database.py
│   ├── test_deduplication.py
│   ├── test_e2e.py
│   ├── test_exporter.py
│   ├── test_rubric.py
│   ├── test_scanner.py
│   └── test_services.py
├── requirements.txt        # Dependencies (fastapi, uvicorn, pytest)
├── hymnody.db              # SQLite database (auto-generated on startup)
└── GEMINI.md               # This project context guide for AI assistants
```

---

## Development Workflow & Rules for AI Agents

1. **Strict Read-Only Access to `/music`**: Never alter, move, rename, or delete any `.m4a` files in the `/music` directory.
2. **Test-Driven Development (TDD)**: Always write unit tests in `tests/` first, verify failure, then write minimal code to pass.
3. **No Heavy Frontend Frameworks**: Use vanilla HTML5, CSS (Tailwind via CDN or CSS variables), and JavaScript to keep the application lightweight and dependency-free.
4. **Environment Variables**:
   - `HYMNODY_DB_PATH`: Path to SQLite database (defaults to `hymnody.db`).
   - `MUSIC_DIR`: Path to `.m4a` audio directory (defaults to `c:\dev\IdeaProjects\hymnody-manager\music`).

---

## Useful Commands

- **Run Test Suite**:
  ```bash
  pytest -v
  ```
- **Start Development Server (LAN & Mobile Testing with Terminal QR Code)**:
  ```bash
  python run_server.py
  ```
- **Start Development Server (Local Only)**:
  ```bash
  uvicorn src.main:app --reload --port 8000
  ```
- **Purge Duplicate Audio Tracks (Dry Run)**:
  ```bash
  python scripts/cleanup_duplicates.py --dry-run
  ```
- **Access App**: Open `http://localhost:8000` (or scanned mobile LAN URL) in browser.


---

## Git Commands & Tool Execution Rule

- **ALWAYS execute git operations via Python subprocess** (e.g. `python -c "import subprocess; subprocess.run(['git', 'commit', '-m', '...'])"`).
- **NEVER chain git commands with semicolons or pass raw git commit strings in PowerShell** to prevent triggering IDE permission dialog pop-ups.

---

## Rules

### NEVER

- Move to planning work during a brainstorming session without asking permission
- Move from planning work to implementation without pausing for review
- Commit to master without suggesting

### ALWAYS

- Use your superpowers to:
    - brainstorm
    - review code
    - manage parallel agents
    - execute plans
    - finish a development branch
    - perform code reviews
    - ask for code reviews
    - use sub agents for development
    - debug issues
    - use a test-driven development (TDD) approach
    - verify code changes before committing them
    - write plans
    - write new skills
    - Pause and ask for a review when you are finished writing specs
    - Ask if you should create a working branch when you are about to start making code changes


