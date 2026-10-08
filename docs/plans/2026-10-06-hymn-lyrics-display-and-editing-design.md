# Hymn Lyrics Display and Editing Design

## 1. Overview
This design introduces hymn lyrics management into the Hymnody Manager web application. Users can view, paste/edit, save, and 1-click copy formatted lyrics directly within the existing Hymn Details Modal (`#hymn-details-modal`) in the desktop planner interface.

The design supports both audio-accompanied hymns and catalog placeholder hymns (printed hymnal entries), making it easy to store lyrics and copy them cleanly into church bulletins, service folders, or presentation slides.

---

## 2. Requirements & Key User Flows

1. **Tabbed Modal Navigation**:
   - Provide two tabs within the Hymn Details Modal body:
     - **Info & History**: Existing Metadata Bar, Service Usage history table, and Shared Tune siblings.
     - **Lyrics**: Dedicated workspace for reading, editing, and copying lyrics.
   - Show a subtle badge or indicator on the **Lyrics** tab when lyrics exist for the active hymn.
2. **Read Mode by Default**:
   - When lyrics exist, display clean formatted text preserving verse and stanza spacing (`white-space: pre-wrap`).
   - Include a **"Copy to Clipboard"** button with toast feedback (*"Lyrics copied to clipboard!"*).
   - Include an **"Edit"** button to transition into Edit Mode.
3. **Edit Mode (Pasting & Editing)**:
   - Provide a spacious multiline text area preloaded with existing lyrics or empty for pasting.
   - Clear placeholder instructions (*"Paste or type hymn lyrics here (separate stanzas with blank lines)..."*).
   - Include a **"Save Lyrics"** button to persist changes to SQLite via the REST API.
   - Include a **"Cancel"** button to discard changes and revert to Read Mode.
4. **Empty State**:
   - When no lyrics exist for a hymn, show a helpful empty state with an **"Add Lyrics"** button that immediately switches to Edit Mode and auto-focuses the text area.
5. **Persistence & Data Model**:
   - Store lyrics in SQLite as a nullable `lyrics TEXT` column on the `hymns` table.
   - Perform an automatic schema migration on startup in `init_db()`.
   - Support updating lyrics via `PUT /api/hymns/{hymn_id}/lyrics`.

---

## 3. Architecture & Components

### 3.1 Database & Backend (`src/database.py`, `src/main.py`)

- **Schema Migration (`src/database.py`)**:
  - In `init_db()`, check if `lyrics` column exists in `hymns` table using `PRAGMA table_info(hymns)`.
  - If missing, execute:
    ```sql
    ALTER TABLE hymns ADD COLUMN lyrics TEXT;
    ```
  - In queries returning hymn details (`get_hymn_by_id`, `get_hymns`, `search_hymns`), include the `lyrics` column.
  - Add helper function `update_hymn_lyrics(hymn_id: int, lyrics: Optional[str], db_path=DEFAULT_DB_PATH) -> bool`.
- **API Endpoints (`src/main.py`)**:
  - `GET /api/hymns/{hymn_id}`: Returns hymn metadata including `lyrics`.
  - `PUT /api/hymns/{hymn_id}/lyrics`:
    - Request payload: `{"lyrics": str}`.
    - Sanitizes and updates the hymn record.
    - Returns updated hymn dictionary or 404 if hymn not found.

### 3.2 Frontend UI & Behavior (`src/static/index.html`, `src/static/styles.css`, `src/static/app.js`)

- **HTML Structure (`src/static/index.html`)**:
  - Within `#hymn-details-modal .modal-body`, insert a tab navigation header:
    - Tab 1: `<button id="tab-btn-info" class="modal-tab-btn active" onclick="switchHymnModalTab('info')">Info & History</button>`
    - Tab 2: `<button id="tab-btn-lyrics" class="modal-tab-btn" onclick="switchHymnModalTab('lyrics')">Lyrics <span id="modal-lyrics-badge" class="badge-dot hidden"></span></button>`
  - Group existing content (warning banner, metadata bar, usage history, sibling tunes) into `<div id="modal-tab-info-content">`.
  - Add `<div id="modal-tab-lyrics-content" class="hidden">`:
    - **Header bar**: Status label, action buttons (`Copy to Clipboard`, `Edit`, `Save`, `Cancel`).
    - **Read View (`#lyrics-read-view`)**: `<div id="lyrics-text" class="lyrics-text-display"></div>`.
    - **Edit View (`#lyrics-edit-view` class="hidden")**: `<textarea id="lyrics-textarea" class="lyrics-textarea" rows="14" placeholder="Paste or type hymn lyrics here (separate stanzas with blank lines)..."></textarea>`.
    - **Empty View (`#lyrics-empty-view` class="hidden")**: Message and `"Add Lyrics"` button.
- **Styling (`src/static/styles.css`)**:
  - Modal tab bar styling (`.modal-tabs`, `.modal-tab-btn`, `.modal-tab-btn.active`).
  - Read-view styling: Clean legible typography, `white-space: pre-wrap`, `line-height: 1.6`, dark theme background.
  - Textarea styling: Resizable vertically, mono/clean sans font, dark theme inputs with focus outline.
  - Responsive height adjustment so text area fits comfortably inside modal bounds.
- **Client Logic (`src/static/app.js`)**:
  - `switchHymnModalTab(tabName)`: Toggles visibility between info and lyrics tab containers.
  - `openHymnDetailsModal(hymnId)`: Populates hymn info, resets active tab to `info`, updates lyrics tab content and indicator dot.
  - `enterLyricsEditMode()`: Switches to edit view, copies current text into textarea, focuses textarea.
  - `cancelLyricsEdit()`: Reverts textarea content, restores read view (or empty view if empty).
  - `saveHymnLyrics()`: Sends `PUT /api/hymns/{id}/lyrics`, updates local hymn cache, transitions to read view, triggers success toast.
  - `copyHymnLyricsToClipboard()`: Writes lyrics text to clipboard via `navigator.clipboard.writeText`, triggers toast *"Lyrics copied to clipboard!"*.

---

## 4. Error Handling & Edge Cases

1. **Clipboard API Support**: Fallback to `document.execCommand('copy')` if `navigator.clipboard` is restricted or unavailable.
2. **Network / Server Errors**: If `PUT /api/hymns/{id}/lyrics` fails, keep textarea in edit mode to preserve user input and display an error toast notification.
3. **Empty Text Submissions**: Trimming empty/whitespace-only input normalizes to `None`/`null` in the database and restores the empty state cleanly.
4. **Modal Reset**: Closing or reopening modal resets tab state gracefully to avoid lingering dirty edit states.

---

## 5. Verification & Testing

1. **Automated Backend Tests (`tests/test_database.py`, `tests/test_api.py`)**:
   - Test DB schema migration adds `lyrics` column without impacting existing data.
   - Test `update_hymn_lyrics` persists and retrieves text correctly.
   - Test `PUT /api/hymns/{hymn_id}/lyrics` with valid text, empty string, and invalid ID (404).
2. **Regression Testing**:
   - Run complete test suite (`python -m pytest -v`) to ensure all 92+ tests continue passing.
3. **Manual UI Verification**:
   - Open Hymn Details modal for a hymn with no lyrics -> verify empty state with "Add Lyrics" button.
   - Paste lyrics with stanzas and save -> verify success toast and clean read-only display.
   - Click "Copy to Clipboard" -> verify toast and test pasting into an external text editor.
   - Click "Edit", modify a stanza, click "Cancel" -> verify changes discarded.
   - Switch between "Info & History" and "Lyrics" tabs -> verify smooth navigation.
