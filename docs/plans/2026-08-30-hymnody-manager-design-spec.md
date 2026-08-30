# Hymnody Manager Design Specification

**Date**: 2026-08-30  
**Status**: Draft for Review  
**Project**: Hymnody Manager & Worship Planner  
**Target Repository**: `c:\dev\IdeaProjects\hymnody-manager`

---

## 1. Executive Summary & Intent

The **Hymnody Manager** is a local Python web application that enables worship planners, pastors, and church volunteers to index, search, and plan church services using their library of `.m4a` audio accompaniment files (specifically *The Concordia Organist* set discs 1–31 and Divine Service 1–5 settings). 

The system solves two primary needs:
1. **Worship Planning**: Fast, intuitive service order creation using Divine Service templates (DS1, DS2, DS3, DS4, DS5, Matins, Vespers), automatically prepopulating liturgical canticles (Kyrie, Gloria, Sanctus, Agnus Dei, Nunc Dimittis) alongside hymn selection slots.
2. **Sanctuary Audio Execution**: Foolproof audio playback during services, either via a local web interface ("Sanctuary Mobile Mode" with oversized touch targets) or by exporting a cleanly numbered `.zip` package containing `.m4a` tracks and `.m3u` playlists for Bluetooth playback on mobile devices (iPads/iPhones/Androids).

---

## 2. Requirements & Constraints

### Functional Requirements
- **FR-1 Metadata Extraction**: Parse MP4 metadata atoms (`©nam`, `trkn`, `disk`, `©alb`, `©ART`, `©day`) and filename patterns (`<disc>-<track> <hymn_number> - <title>.m4a`) from all audio files in `/hymns`.
- **FR-2 Hymn Catalog & Search**: Provide search by hymn number, title, disc number, or liturgical season.
- **FR-3 Divine Service Presets**: Provide template presets for Divine Service 1–5, Matins, Vespers, etc., inserting appropriate ordinaries (Kyrie, Gloria, Sanctus, Agnus Dei, Nunc Dimittis, etc.) in correct order.
- **FR-4 Service Order Builder**: Allow adding, removing, reordering, and slotting hymns into service plans.
- **FR-5 Audio Streaming**: Serve `.m4a` files over HTTP Range Requests (`206 Partial Content`) for browser seeking and jumping.
- **FR-6 Transport Controls**: Full playback controls (`⏮ Prev`, `⏯ Play/Pause`, `⏭ Next`, timeline scrubber, track click-jump, keyboard shortcuts).
- **FR-7 Mobile Zip Export**: Export a service order as a `.zip` archive containing sequentially numbered audio tracks (`01_Opening_Hymn.m4a`, `02_DS2_Kyrie.m4a`, ...) and an `.m3u` playlist file.
- **FR-8 Sanctuary Mobile Mode**: Responsive, touch-friendly UI mode with large buttons for non-technical volunteers.

### Non-Functional & Constraints
- **NFR-1 Pure Local Execution**: Must run completely offline with no external cloud dependencies.
- **NFR-2 Non-Destructive**: Read-only access to `/hymns`. Never modify or delete original audio files.
- **NFR-3 Standard Python Stack**: Python 3.11+, FastAPI, Uvicorn, SQLite3 (standard library), vanilla HTML5/JS/CSS (zero heavy npm node_modules).

---

## 3. Detailed Component Architecture

### Component Diagram

```
+-------------------------------------------------------------------------------+
|                             Hymnody Manager App                               |
+-------------------------------------------------------------------------------+
|                                                                               |
|  +-------------------------+             +---------------------------------+  |
|  |     /hymns Folder       |             |         SQLite Database         |  |
|  | (~375+ .m4a audio files)|             |          (hymnody.db)           |  |
|  +------------+------------+             +----------------+----------------+  |
|               |                                           ^                   |
|      (Read-Only Ingestion)                                | SQL Queries       |
|               v                                           v                   |
|  +-------------------------+             +---------------------------------+  |
|  |  Metadata Scanner       |------------>|      Repository Layer           |  |
|  |  (src/scanner.py)       |             |      (src/database.py)         |  |
|  +-------------------------+             +----------------+----------------+  |
|                                                           ^                   |
|                                                           | API Data          |
|                                                           v                   |
|                                          +---------------------------------+  |
|                                          |       FastAPI Web Routes        |  |
|                                          |       (src/main.py)             |  |
|                                          +----------------+----------------+  |
|                                                           ^                   |
|                                                           | REST / Stream /   |
|                                                           | Zip Export        |
|                                                           v                   |
|                                          +---------------------------------+  |
|                                          |      Frontend Web Interface     |  |
|                                          |  - Desktop Worship Planner      |  |
|                                          |  - Sanctuary Mobile Mode        |  |
|                                          +---------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 4. Data Schemas

### `hymnody.db` Relational Schema

```sql
CREATE TABLE IF NOT EXISTS hymns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hymn_number INTEGER,
    title TEXT NOT NULL,
    disc_number INTEGER NOT NULL,
    track_number INTEGER NOT NULL,
    album TEXT,
    artist TEXT,
    year INTEGER,
    file_path TEXT NOT NULL UNIQUE,
    liturgical_season TEXT
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_date TEXT NOT NULL,
    title TEXT NOT NULL,
    setting_preset TEXT, -- 'DS1', 'DS2', 'DS3', 'DS4', 'DS5', 'Matins', 'Vespers'
    liturgical_color TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    hymn_id INTEGER, -- Nullable for liturgical canticles without a specific hymn record
    item_title TEXT NOT NULL,
    slot_name TEXT NOT NULL,
    sequence_order INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    FOREIGN KEY (hymn_id) REFERENCES hymns(id)
);
```

---

## 5. Divine Service Settings Map

| Setting Preset | Liturgical Canticle Tracks Included | Hymn Slots Prepopulated |
|---|---|---|
| **DS1** | DS1 Kyrie, DS1 Gloria / This is Feast, DS1 Offertory, DS1 Sanctus, DS1 Agnus Dei, DS1 Nunc Dimittis | Opening, Hymn of Day, Distribution 1 & 2, Closing |
| **DS2** | DS2 Kyrie, DS2 Gloria in Excelsis, DS2 Offertory, DS2 Sanctus, DS2 Agnus Dei, DS2 Nunc Dimittis | Opening, Hymn of Day, Distribution 1 & 2, Closing |
| **DS3** | DS3 Kyrie, DS3 Gloria in Excelsis, DS3 Offertory, DS3 Sanctus, DS3 Agnus Dei, DS3 Nunc Dimittis | Opening, Hymn of Day, Distribution 1 & 2, Closing |
| **DS4** | DS4 Kyrie, DS4 This is the Feast, DS4 Sanctus, DS4 Agnus Dei, DS4 Nunc Dimittis | Opening, Hymn of Day, Distribution 1 & 2, Closing |
| **DS5** | DS5 Kyrie, DS5 Gloria, DS5 Sanctus, DS5 Agnus Dei, DS5 Nunc Dimittis | Opening, Hymn of Day, Distribution 1 & 2, Closing |
| **Matins** | Venite, Te Deum / Benedictus | Invocation, Office Hymn, Canticle Hymn |
| **Vespers** | Phos Hilaron, Psalmody, Magnificat | Invocation, Office Hymn, Closing Hymn |

---

## 6. Mobile Export Specification

When exporting a service plan via `GET /api/services/{id}/export/zip`:
1. The backend creates an in-memory or temp `.zip` archive named `{date}_{service_title}.zip`.
2. Each item in `service_items` is copied into the zip as a sequentially padded `.m4a` file:
   - `01_Opening_Hymn_331_The_advent_of_our_King.m4a`
   - `02_DS2_Kyrie.m4a`
   - `03_DS2_Gloria_in_Excelsis.m4a`
   - `04_Hymn_of_the_Day_332_Savior_of_the_nations_come.m4a`
   - `05_DS2_Sanctus.m4a`
   - `06_DS2_Agnus_Dei.m4a`
   - `07_Distribution_558_Not_unto_us.m4a`
   - `08_DS2_Nunc_Dimittis.m4a`
   - `09_Closing_Hymn_603_We_know_that_Christ_is_raised.m4a`
3. A playlist file `playlist.m3u` is generated inside the zip listing all filenames in sequence.

---

## 7. Verification & Acceptance Criteria

- **Scanner Verification**: 100% of `.m4a` files in `/hymns` successfully indexed into SQLite without errors.
- **API Tests**: Automated `pytest` suite testing database creation, search queries, service creation, item reordering, range audio streaming, and zip export.
- **UI Verification**: Verified desktop planner drag/drop service building and Sanctuary Mobile Mode UI playback on touchscreen/mobile viewport.
