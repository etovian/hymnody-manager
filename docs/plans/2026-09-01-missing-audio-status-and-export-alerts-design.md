# Design Document: Missing Audio Status Indicators & Export Alerts

**Date**: 2026-09-01  
**Status**: Approved  
**Author**: Hymnody Manager Team  

---

## 1. Overview & Problem Statement

In Hymnody Manager worship services (such as Matins), certain liturgical canticles (e.g. `Venite`, `Te Deum`) may not automatically find matching `.m4a` audio files if the underlying audio disc set lacks those specific tracks (e.g. Disc 31).

Previously:
1. Unbound slots had empty `file_path`s without clear visual feedback in the Planner UI or transport controls.
2. Clicking **Export Mobile Zip** silently omitted unbound items while leaving sequence number gaps (`01`, `03`, `05`) without alerting the user prior to download.

---

## 2. Requirements & Goals

1. **Visual Audio Status Badges**: Display explicit status badges (`🎵 Audio Ready` vs `⚠️ Missing Audio`) on service item cards in the Desktop Planner view.
2. **Disabled Transport State**: Disable the **▶ Play** button for items without bound audio to prevent silent playback failures.
3. **Preserved Export Track Numbering**: Retain original 1-based sequence numbering (`01`, `03`, `05`) for exported `.m4a` files and `playlist.m3u` when intermediate items have no audio.
4. **Pre-Export Warning Confirmation**: Show a clear confirmation alert when exporting a service plan with missing audio files, listing the skipped items and allowing the user to cancel or proceed.

---

## 3. Detailed Component Design

### 3.1 Desktop & Sanctuary UI Updates (`src/static/app.js` & `styles.css`)

- **Item Card Status Badges**:
  - Bound Audio: Green pill badge (`🎵 Audio Ready`).
  - Missing Audio: Amber/Red badge (`⚠️ Missing Audio`) with prompt *"No audio file attached (Drag track here to bind)"*.
- **Transport Controls**:
  - `playServiceTrack(index)` checks if `item.file_path` exists. If missing, displays a toast notification: `"No audio file bound to this item."`
  - Play button rendered with `btn-disabled` / `⚠️ No Audio` styling when no audio file is bound.
- **Sanctuary Mobile View**:
  - Unbound items styled with `[Unbound]` subtitle and skipped during auto-advance.

### 3.2 Mobile ZIP Exporter (`src/exporter.py`)

- Maintain original `sequence_order` for exported filenames:
  ```python
  clean_title = re.sub(r'[\/:*?"<>|]', '_', f"{slot}_{raw_title}").replace(' ', '_')
  filename = f"{item['sequence_order']:02d}_{clean_title}.m4a"
  ```
- Write available tracks to ZIP archive with preserved indices (`01_...m4a`, `03_...m4a`, `05_...m4a`).
- Construct `playlist.m3u` referencing the exact preserved filenames.

### 3.3 Export Confirmation Dialog (`src/static/app.js`)

- In `exportMobileZip()`:
  - Inspect `currentService.items` for items where `!item.file_path`.
  - If missing audio items exist, prompt the user with `confirm(...)`:
    > *"Notice: 2 items (02 - Venite, 04 - Te Deum) have no audio files attached and will not be in the zip package. Track numbering (01, 03, 05) will be preserved in the playlist. Export anyway?"*
  - If user cancels, abort export so they can bind audio tracks.

---

## 4. Verification & Testing Plan

### 4.1 Automated Tests (`tests/test_exporter.py` & `tests/test_api.py`)
- `test_export_service_zip_preserves_numbering_with_missing_files`: Verify `01`, `03`, `05` filenames in zip archive and `playlist.m3u`.
- `test_service_details_contains_file_path_and_hymn_id`: Verify items return `file_path` field for UI state rendering.

### 4.2 Manual Testing
1. Load a Matins service plan.
2. Verify `Venite` and `Te Deum` display `⚠️ Missing Audio` badges.
3. Click **Export Mobile Zip** and verify confirmation dialog lists skipped items.
4. Confirm download and check ZIP archive contains `01_...`, `03_...`, `05_...` and `playlist.m3u`.
