# Hymnody Manager Design Document

**Date**: 2026-08-30  
**Project**: Hymnody Manager & Worship Planner  
**Target Repository**: `c:\dev\IdeaProjects\hymnody-manager`

---

## 1. Overview & Purpose

The **Hymnody Manager** is a local Python web application designed for Lutheran worship planning, hymn cataloging, and service audio playlist management. It extracts MP4 metadata tags (`©nam`, `trkn`, `disk`, `©alb`, `©ART`, `©day`) and filename structures from `.m4a` audio files (such as *The Concordia Organist* set in `/hymns`), indexes them in a local SQLite database (`hymnody.db`), and provides a clean browser interface for searching hymns, building service orders, playing service audio, and exporting mobile-ready audio packages for church sanctuary Bluetooth playback.

---

## 2. System Architecture

```
                                +-------------------------+
                                |      /hymns Folder      |
                                |  (~375+ .m4a audio)     |
                                +------------+------------+
                                             |
                                  Metadata Ingestion
                                             v
                                +-------------------------+
                                |       scanner.py        |
                                | (MP4 atom/tag parsing)  |
                                +------------+------------+
                                             |
                                             v
                                +-------------------------+
                                |   SQLite (hymnody.db)   |
                                +------------+------------+
                                             ^
                                             | REST / Audio / Zip Export
                                             v
                                +-------------------------+
                                |    FastAPI (main.py)    |
                                +------------+------------+
                                             ^
                                             | HTTP / Web UI
                                             v
                                +-------------------------+
                                |  Worship Builder UI     |
                                |  - Full Desktop Planner |
                                |  - Sanctuary Mobile Mode|
                                +-------------------------+
```

---

## 3. Database Schema (`hymnody.db`)

### `hymns`
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `hymn_number`: INTEGER (e.g. `331`, `558`, `603`)
- `title`: TEXT (e.g. *"The advent of our King"*)
- `disc_number`: INTEGER (e.g. `1`, `30`)
- `track_number`: INTEGER (e.g. `1`, `25`)
- `album`: TEXT (e.g. *"The Concordia Organist"*)
- `artist`: TEXT (e.g. *"Concordia Publishing House"*)
- `year`: INTEGER (`2009`)
- `file_path`: TEXT (Relative path to `.m4a` file)
- `liturgical_season`: TEXT (Inferred from hymnal index ranges)

### `services`
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `service_date`: TEXT (ISO Date `YYYY-MM-DD`)
- `title`: TEXT (e.g. *"1st Sunday in Advent"*)
- `setting_preset`: TEXT (e.g. `DS1`, `DS2`, `DS3`, `DS4`, `DS5`, `Matins`, `Vespers`)
- `liturgical_color`: TEXT (e.g. *Blue*, *Violet*, *White*, *Green*, *Red*)
- `notes`: TEXT

### `service_items`
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `service_id`: INTEGER (FOREIGN KEY -> `services.id`)
- `hymn_id`: INTEGER (FOREIGN KEY -> `hymns.id`, NULL for custom liturgical items)
- `item_title`: TEXT (e.g. *"DS2 Kyrie"*, *"Savior of the Nations, Come"*)
- `slot_name`: TEXT (e.g. *"Invocation / Opening Hymn"*, *"Kyrie"*, *"Hymn of the Day"*, *"Sanctus"*, *"Distribution 1"*, *"Closing"*)
- `sequence_order`: INTEGER
- `file_path`: TEXT (Path to track audio file)

---

## 4. API Specification

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scan` | Rescans `/hymns` folder and updates SQLite database |
| `GET` | `/api/hymns` | Search and filter hymns (`?q=`, `?season=`, `?disc=`) |
| `GET` | `/api/hymns/{id}` | Retrieve specific hymn details |
| `GET` | `/api/hymns/{id}/audio` | Stream `.m4a` audio file with HTTP 206 Range support |
| `GET` | `/api/services` | List created service plans |
| `POST` | `/api/services` | Create new service plan (with option for setting preset like `DS2`) |
| `GET` | `/api/services/{id}` | Retrieve service plan with ordered items |
| `PUT` | `/api/services/{id}/items` | Update item ordering, slot names, and hymn selections |
| `DELETE` | `/api/services/{id}` | Delete a service plan |
| `GET` | `/api/services/{id}/export/zip` | Export downloadable `.zip` package of sequentially numbered `.m4a` tracks (`01_Opening_Hymn.m4a`, `02_DS2_Kyrie.m4a`) + `.m3u` playlist |
| `GET` | `/api/services/{id}/export/m3u` | Export `.m3u8` playlist file |

---

## 5. User Interface Modes & Mobile Support

### Desktop Planning Mode
- Search & filter hymn database by number, title, or liturgical season.
- Select Divine Service settings (**DS1, DS2, DS3, DS4, DS5, Matins, Vespers**) to pre-fill liturgical ordinaries.
- Drag and drop or reorder service items.
- One-click export to Mobile Audio Package (`.zip` containing numbered tracks and `.m3u`).

### Sanctuary Mobile Mode
- Streamlined touch UI designed for volunteers operating music over Bluetooth on a tablet/phone connected to local network.
- High-contrast, large text displaying current & upcoming tracks.
- Oversized touch controls: **[ PLAY / PAUSE ]**, **[ NEXT TRACK ]**, **[ PREVIOUS TRACK ]**.
- Direct track jump list.

---

## 6. Testing & Resilience

- **Parser Resiliency**: Fallback regex parsing extracts disc/track/number/title from filenames if tags are missing.
- **Audio Error Handling**: Visual indicators for unreadable files with automatic skip to next playable track.
- **Automated Tests**: Unit tests with `pytest` covering tag extraction, SQLite queries, zip export generation, and FastAPI routes.
