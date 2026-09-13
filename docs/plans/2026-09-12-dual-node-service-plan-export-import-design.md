# Dual Node Service Plan Export/Import & UI Real Estate Design

## Problem & Objectives

To support using Hymnody Manager across both home (service planning) and church (service execution) without exposing copyrighted audio files (`.m4a`) to the public internet, the application uses a **Dual Node** architecture. 

In this model:
- Both Home and Church computers store local copies of the `.m4a` music collection on disk.
- Zero audio files are transmitted across the internet.
- Worship service plans created at home are transferred to the church computer via lightweight, portable `.hymnody` JSON files.
- The Worship Planner header UI is streamlined to accommodate export options and optimize space.

---

## 1. Portable Service Plan File Schema (`.hymnody`)

When exporting a service plan, the application generates a portable JSON payload containing metadata and resilient hymn match identifiers.

### File Schema (`.hymnody`)
```json
{
  "version": "1.0",
  "exported_at": "2026-09-12T18:30:00Z",
  "service": {
    "title": "Second Sunday in Advent",
    "preset_name": "Divine Service 1",
    "date": "2026-12-06",
    "notes": "Organist: John Doe",
    "items": [
      {
        "slot_name": "Invocation Hymn",
        "item_type": "hymn",
        "hymn_number": 331,
        "title": "The Advent of Our King",
        "disc": 1,
        "track": 5,
        "tune": "ST. THOMAS",
        "setting": "The Concordia Organist"
      },
      {
        "slot_name": "Kyrie",
        "item_type": "ordinary",
        "title": "Kyrie (DS1)",
        "disc": 30,
        "track": 2
      }
    ]
  }
}
```

### Hymn Audio Matching Algorithm on Import
When importing a `.hymnody` file at a target node (e.g., Church PC):
1. **Primary Match**: Search `hymnody.db` by `(disc, track)`.
2. **Secondary Match**: Search `hymnody.db` by `(hymn_number, title)`.
3. **Status Check**: Verify if the target node's local audio file actually exists at `file_path`.
4. **Resolution**:
   - If found: Bind item to target node's local `hymn_id`.
   - If missing: Create service item entry with missing audio alert status.

---

## 2. UI & Component Design

### Unified Export Dropdown
To conserve header real estate, the existing standalone `"Export Mobile Package"` button is replaced with a clean **"Export ▾"** dropdown menu:
- **Mobile Audio Package (.zip)**: Downloads zip containing renamed audio files + `playlist.m3u`.
- **Service Plan File (.hymnody)**: Downloads portable JSON service plan.

### Header Layout & Space Optimization
- **Inline Title & Rubric Badge**: Move the Rubric Verification Badge (e.g., `Standard DS1 Rubric [✓]`) onto the same horizontal line as the Service Title (`Service Plan: Sunday Worship Service`).
- **Fix Premature Title Wrapping**: Adjust CSS flex containers (`flex-wrap`, `white-space`, `gap`, `align-items`) in `src/static/styles.css` to allow title text to expand across available horizontal space.
- **Import Button & Drag-and-Drop**: Add an **"Import Plan"** button next to **"Export ▾"** and support dragging `.hymnody` files directly onto the app window.

```
+---------------------------------------------------------------------------------+
| Service Plan: Second Sunday in Advent  [✓ DS1 Rubric]       [Import] [Export ▾] |
|                                                                  | Mobile Zip   |
|                                                                  | Service File |
+---------------------------------------------------------------------------------+
```

### Import Confirmation Modal
Presents a preview of the imported plan before saving to `hymnody.db`:
- Title, Date, Preset, and total Item count.
- Audio verification summary (e.g., *"All 6 hymn audio files matched on local disk"*).
- Buttons: `Confirm Import` and `Cancel`.

---

## 3. Backend API Endpoints (`src/main.py` & `src/services.py`)

1. **`GET /api/services/{service_id}/export-plan`**
   - Fetches service details & items.
   - Formats `.hymnody` JSON structure.
   - Returns streaming JSON file response with `Content-Disposition: attachment; filename="[Date]_[Title].hymnody"`.

2. **`POST /api/services/import-plan`**
   - Receives `.hymnody` JSON payload.
   - Validates schema version.
   - Resolves items against target node database.
   - Inserts new service record in `hymnody.db`.
   - Returns imported service ID and match summary.

---

## 4. Error Handling & Validation

- **Invalid File Format**: Returns `400 Bad Request` with message *"Invalid service plan file format"*.
- **Duplicate Name Handling**: If a service with identical title and date exists, the imported service title is saved with `(Imported)` suffix.
- **Schema Migration**: Explicit `version` field enables backwards compatibility for future plan format updates.

---

## 5. Automated Verification & Testing

- **`tests/test_exporter.py`**: Test `.hymnody` JSON export formatting and round-trip parsing.
- **`tests/test_api.py`**: Test export download endpoint and import POST endpoint.
- **`tests/test_services.py`**: Unit tests for audio track matching resolution across different database instances.
