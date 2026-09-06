# Design Specification: Dynamic Export Zip Filename

**Date**: 2026-09-01  
**Status**: Approved  

---

## 1. Overview

When exporting a service package as a `.zip` file for mobile/sanctuary playback, the zip file name must be dynamically constructed to include:
1. **Serial Date**: 8-digit date string (`YYYYMMDD`).
2. **Order of Service**: Setting preset (e.g., `DS3`, `Matins`, `Vespers`).
3. **Liturgical Day**: Liturgical day string if present (e.g., `Pentecost 15`).

**Example concatenated filenames**:
- With Liturgical Day: `20260901_DS3_Pentecost_15.zip`
- Without Liturgical Day: `20260901_Matins.zip`

---

## 2. Filename Generation Algorithm

The logic will be encapsulated in `generate_export_filename(service: dict) -> str` inside `src/exporter.py`.

### Formatting & Sanitization Rules
1. **Serial Date (`YYYYMMDD`)**:
   - Extracted from `service['service_date']` (e.g. `"2026-09-01"` -> `"20260901"`).
   - If missing or unparseable, defaults to today's date in `YYYYMMDD`.
2. **Order of Service (Setting Preset)**:
   - Uses `service['setting_preset']` (e.g., `"DS3"`).
   - Spaces and filesystem-unsafe characters (`/:*?"<>|`) are replaced with underscores (`_`).
   - If missing, defaults to `"Service"`.
3. **Liturgical Day** *(Optional)*:
   - Uses `service['liturgical_day']`.
   - Spaces and filesystem-unsafe characters are replaced with underscores (`_`).
   - If empty, `None`, or whitespace-only, this segment is omitted entirely.
4. **Assembly**:
   - Segments are joined with `_`.
   - Multiple consecutive underscores are collapsed to a single `_`.
   - Filename is appended with `.zip`.

---

## 3. Data Flow & Component Changes

### `src/exporter.py`
- `generate_export_filename(service: dict) -> str`: Pure helper to compute zip filename.
- `export_service_zip(service_id: int, db_path="hymnody.db") -> tuple[bytes | None, str | None]`:
  - Fetches service details via `get_service_details`.
  - Returns `(None, None)` if service is missing or empty.
  - Builds filename via `generate_export_filename(service)`.
  - Creates zip archive bytes.
  - Returns `(zip_bytes, filename)`.

### `src/main.py`
- Updates `GET /api/services/{service_id}/export/zip`:
  ```python
  zip_bytes, filename = export_service_zip(service_id, db_path=get_db_path())
  if not zip_bytes:
      raise HTTPException(status_code=404, detail="Service not found or empty")
  return Response(
      content=zip_bytes,
      media_type="application/zip",
      headers={
          "Content-Disposition": f'attachment; filename="{filename}"'
      }
  )
  ```

---

## 4. Track Sequence Integrity & Missing Audio Handling

- Audio tracks inside the zip (`01_Invocation_...m4a`, `03_Gloria_...m4a`) retain their 1-indexed `sequence_order`.
- If track 2 lacks an audio file, track 3 remains `03_...m4a` and is **not** re-indexed to `02`. This makes missing files immediately visible to sanctuary operators.

---

## 5. Verification & Testing

- Unit tests in `tests/test_exporter.py`:
  - Full filename formatting (`20260901_DS3_Pentecost_15.zip`).
  - Omitted liturgical day (`20260901_DS3.zip`).
  - Sanitization of spaces and invalid characters.
  - Tuple return `(zip_bytes, filename)`.
  - Track sequence gap preservation when audio file is missing.
- Integration tests in `tests/test_main.py`:
  - `GET /api/services/{service_id}/export/zip` header validation.
