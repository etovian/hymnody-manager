# Exported Playlist Sorting & Naming Design

## Overview
When exporting worship services as mobile audio packages (`.zip`), the zip archive contains numbered audio track files (`01_Invocation_Hymn_331.m4a`, `02_DS2_Kyrie.m4a`, etc.) along with a playlist file (`.m3u`). Previously, the playlist was named either `playlist.m3u` or `<base_name>.m3u` (e.g., `20261025_DS3_Common_Pentecost_22.m3u`). 

Standard lexicographical sorting in desktop and mobile file explorers (Windows File Explorer, macOS Finder, iOS Files, Android File Manager) places `2026...` after numeric track prefixes (`01_`, `02_`, etc.), causing the playlist file to be scattered amidst or below audio tracks.

This design introduces a `00_` prefix to the exported playlist filename inside the zip package to guarantee that the playlist file sorts at position #0 (the very top) of the exported folder list.

---

## Technical Specifications

### 1. Playlist Naming Logic (`src/exporter.py`)
- **Zip Archive Name**: `<date>_<preset>_<liturgical_day>.zip` (e.g., `20261025_DS3_Common_Pentecost_22.zip`).
- **Base Name Extraction**: `<base_name>` = `filename[:-4]` (e.g., `20261025_DS3_Common_Pentecost_22`).
- **Playlist Archive Entry Name**: `00_<base_name>.m3u` (e.g., `00_20261025_DS3_Common_Pentecost_22.m3u`).

### 2. File Explorer Sorting Alignment
- **Audio Tracks**: `01_<slot>_<title>.m4a`, `02_<slot>_<title>.m4a`, ...
- **Playlist File**: `00_<base_name>.m3u`
- **Result**: `00_` numerically and lexicographically precedes `01_`, ensuring instant visibility of the playlist at the top of the file list for non-technical sanctuary volunteers.

---

## Verification Plan

### Automated Tests (`tests/test_exporter.py`)
1. Verify that `export_service_zip` names the `.m3u` entry inside the zip as `00_<base_name>.m3u`.
2. Confirm that neither `playlist.m3u` nor un-prefixed `<base_name>.m3u` exist in the output zip archive.
3. Run `pytest -v` across all 75+ automated unit and integration tests.
