# Hymn Details & Historical Usage Modal Design Document

## Overview
This design document specifies the enhancement of the Hymnal Catalog in Hymnody Manager. Users will be able to inspect detailed metadata for any hymn, view its historical worship service usages (dates, liturgical days, settings, and slots), and discover all other hymns in the catalog that share the same tune.

---

## 1. User Experience & Interface Design

### 1.1 Catalog Entry Point
In the Hymnal Catalog list ([`src/static/app.js`](file:///c:/dev/IdeaProjects/hymnody-manager/src/static/app.js)), each hymn item is updated with an **Info (`ℹ️`)** button alongside the preview `▶ Play` button:
- Clicking either the `ℹ️` button or the hymn title opens the **Hymn Details Modal**.
- Sibling hymns can also be navigated within the modal.

### 1.2 Modal Structure ([`src/static/index.html`](file:///c:/dev/IdeaProjects/hymnody-manager/src/static/index.html) & [`src/static/styles.css`](file:///c:/dev/IdeaProjects/hymnody-manager/src/static/styles.css))
The modal adheres to the application's slate dark theme palette:
1. **Header**:
   - Title: `[LSB <Number>] - <Hymn Title>` (or `<Liturgy Title>` for liturgical canticles).
   - Close (`✕`) button in the top right.
   - Closed on backdrop click or `Escape` key press.
2. **Metadata Summary Bar**:
   - `🎵 Tune: <Tune Name>` badge.
   - `Liturgical Season: <Season>` pill.
   - `Source: <Source Meaning>` pill (e.g. *Paul Gerhardt*, *Martin Luther*).
   - `Audio Status`: `Disc <D>, Track <T>` (if present) or `No Audio Track` badge.
3. **Previous Service Usage Section**:
   - Title with count: `Previous Service Usage (<N>)`.
   - Data table with columns:
     - `Date` (e.g. `2026-04-05`)
     - `Liturgical Day` (e.g. `Easter Sunday`)
     - `Setting` (e.g. `DS3`, `DS1`, `Matins`)
     - `Service Title` (e.g. `The Resurrection of Our Lord`)
     - `Slot` (e.g. `Hymn of the Day`, `Distribution 1`)
   - Empty state: *"No previous service usage recorded for this hymn."*
4. **Other Hymns Sharing the Same Tune Section**:
   - Title with count: `Other Hymns Sharing Tune: <Tune Name> (<N>)`.
   - Card list for sibling hymns:
     - Badge with LSB number, hymn title, and season.
     - `▶ Play` button for preview audio (if audio file exists).
     - Clicking on the card switches the modal to inspect that sibling hymn.
   - Empty state: *"No other hymns in the catalog share this tune."* (or *"No tune assigned."*).

---

## 2. Backend & Data Architecture

### 2.1 Database Queries ([`src/database.py`](file:///c:/dev/IdeaProjects/hymnody-manager/src/database.py))

1. **`get_hymn_usage_history(hymn_id: int, db_path: str = DEFAULT_DB_PATH) -> list[dict]`**:
   ```sql
   SELECT s.id AS service_id,
          s.service_date,
          s.title AS service_title,
          s.liturgical_day,
          s.setting_preset,
          si.slot_name,
          si.sequence_order
   FROM service_items si
   JOIN services s ON si.service_id = s.id
   WHERE si.hymn_id = ?
   ORDER BY s.service_date DESC, s.id DESC
   ```

2. **`get_hymns_sharing_tune(tune_id: int, exclude_hymn_id: int = None, db_path: str = DEFAULT_DB_PATH) -> list[dict]`**:
   ```sql
   SELECT h.id, h.hymn_number, h.title, h.liturgical_season,
          h.disc_number, h.track_number, h.file_path,
          t.name AS tune_name, s.meaning AS source_meaning
   FROM hymns h
   LEFT JOIN tunes t ON h.tune_id = t.id
   LEFT JOIN sources s ON h.source_code = s.code
   WHERE h.tune_id = ? AND (h.id != ? OR ? IS NULL)
   ORDER BY CASE WHEN h.hymn_number IS NOT NULL THEN 0 ELSE 1 END ASC,
            h.hymn_number ASC, h.title ASC
   ```

### 2.2 API Endpoint ([`src/main.py`](file:///c:/dev/IdeaProjects/hymnody-manager/src/main.py))
Enhance `GET /api/hymns/{hymn_id}`:
- Retrieves base hymn record with tune and source meanings via `get_hymn_by_id(hymn_id)`.
- If found, fetches and attaches:
  - `usage_history`: Result of `get_hymn_usage_history(hymn_id)`.
  - `same_tune_hymns`: Result of `get_hymns_sharing_tune(tune_id, exclude_hymn_id=hymn_id)`.
- Returns enriched JSON object, or 404 if not found.

---

## 3. Frontend Architecture & Flow ([`src/static/app.js`](file:///c:/dev/IdeaProjects/hymnody-manager/src/static/app.js))

1. **`openHymnDetailsModal(hymnId)`**:
   - Opens `#hymn-details-modal` with loading indicator.
   - Fetches `/api/hymns/${hymnId}`.
   - Renders header, metadata badges, usage history table, and same-tune cards.
2. **`closeHymnDetailsModal()`**:
   - Hides `#hymn-details-modal`.
3. **`playModalHymnAudio(hymnId)`**:
   - Plays audio preview using the existing audio player bar.
4. **Keyboard & Event listeners**:
   - Closes modal on Escape key or backdrop click.

---

## 4. Verification & Testing Strategy

1. **Database Unit Tests ([`tests/test_database.py`](file:///c:/dev/IdeaProjects/hymnody-manager/tests/test_database.py))**:
   - Test `get_hymn_usage_history` returns correct services, dates, liturgical settings, and slot names in descending order.
   - Test `get_hymns_sharing_tune` finds sibling hymns sharing a tune ID and excludes the queried hymn.
2. **API Tests ([`tests/test_api.py`](file:///c:/dev/IdeaProjects/hymnody-manager/tests/test_api.py))**:
   - Test `GET /api/hymns/{hymn_id}` returns the enriched structure with `usage_history` and `same_tune_hymns`.
3. **E2E & DOM Tests ([`tests/test_e2e.py`](file:///c:/dev/IdeaProjects/hymnody-manager/tests/test_e2e.py))**:
   - Verify modal elements exist in `index.html`.
   - Test opening modal, rendering history, rendering sibling hymns, and closing modal.
