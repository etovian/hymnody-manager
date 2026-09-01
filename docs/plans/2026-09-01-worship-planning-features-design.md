# Worship Planning Features Design Spec

**Date**: 2026-09-01  
**Project**: Hymnody Manager & Worship Planner  
**Status**: Approved Design Spec  

---

## 1. Overview & Goals

This feature update enhances the worship planning experience in **Hymnody Manager** by introducing:
1. **Worship Date Selection & Liturgical Metadata**: Allowing users to select any future (or past) worship date and specify liturgical metadata (e.g., day of the liturgical calendar).
2. **Services Explorer**: A dedicated modal interface to browse, filter, search, load, duplicate, or delete saved worship service plans.
3. **Dual-Zone Drag-and-Drop**: Allowing users to drop items onto the service plan to either **insert** between items (top/bottom ~25% zone) or **replace** an existing slot (middle ~50% zone).
4. **Database-Backed Editable Templates**: Moving built-in presets (DS1–DS5, Matins, Vespers) into SQLite tables (`service_templates` and `template_items`), correcting missing items (such as the DS3 Salutation and Collect Amen), and providing a Template Editor UI.
5. **Historical Service Persistence & Analytics Foundation**: Archiving full service playlists for past/future dates to lay the groundwork for hymn usage frequency analysis.

---

## 2. System Architecture & Component Changes

### 2.1 Database Schema (`src/database.py`)

#### `service_templates` Table
Stores high-level preset definitions.
```sql
CREATE TABLE IF NOT EXISTS service_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_builtin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `template_items` Table
Stores slot sequences for each template.
```sql
CREATE TABLE IF NOT EXISTS template_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    slot_name TEXT NOT NULL,
    match_term TEXT,
    item_title TEXT NOT NULL,
    sequence_order INTEGER NOT NULL,
    is_hymn_slot BOOLEAN DEFAULT 0,
    FOREIGN KEY (template_id) REFERENCES service_templates(id) ON DELETE CASCADE
);
```

#### Enhanced `services` Table
Stores individual service plans.
```sql
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_date TEXT NOT NULL,
    title TEXT NOT NULL,
    liturgical_day TEXT,
    setting_preset TEXT,
    liturgical_color TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2.2 Template Seeding & Preset Corrections (`src/services.py`)

On application startup, if `service_templates` is empty, the backend automatically seeds standard LCMS presets into the database.

#### DS3 Template Corrections:
Standard DS3 is updated to include all missing ordinaries:
1. Invocation / Opening Hymn (Hymn Slot)
2. Kyrie (`DS3 - Kyrie`)
3. Gloria in Excelsis (`DS3 - Gloria in Excelsis`)
4. Salutation & Collect (`DS3 - Salutation` / `DS3 - Collect of the Day`)
5. Collect Amen (`DS3 - Collect Amen`)
6. Hymn of the Day (Hymn Slot)
7. Offertory (`DS3 - Offertory`)
8. Sanctus (`DS3 - Sanctus`)
9. Agnus Dei (`DS3 - Agnus Dei`)
10. Distribution Hymn 1 (Hymn Slot)
11. Nunc Dimittis (`DS3 - Nunc Dimittis`)
12. Closing Hymn (Hymn Slot)

---

### 2.3 Frontend & Interaction Design (`src/static/`)

#### 1. Worship Date & Metadata Picker
- Header features `<input type="date" id="service-date-input">` bound to `currentService.service_date`.
- Text field for `liturgical_day` (e.g. "15th Sunday after Trinity").
- Date changes automatically update the service record in SQLite.

#### 2. Services Explorer Modal
- Accessible via "Services Explorer" button in the right panel header.
- Features search filter (by date or title/liturgical day) and tabs (**Upcoming**, **Past**, **All**).
- List items show date, title, setting preset, track count, with action buttons: **Load**, **Duplicate**, **Delete**, **Export Zip**.

#### 3. Dual-Zone Drag-and-Drop
- During `dragover` on a service item row:
  - If cursor offset is in **top 25% or bottom 25%**: apply `insert-above` or `insert-below` CSS class (blue line indicator). Dropping **inserts** a new track before/after the item.
  - If cursor offset is in **middle 50%**: apply `replace-target` CSS class (card glow). Dropping **replaces** the target slot track.
- Supports both catalog-to-plan drop and plan-item-reorder drop.

#### 4. Template Editor Modal
- Displays built-in and user-created templates.
- Allows adding, editing, deleting, or reordering slots.
- Option to duplicate an existing LCMS preset to build a custom service template.

---

### 2.4 Dynamic Rubric Validation & Analytics API

#### Dynamic Rubric Validation
- Queries database template items for the assigned preset name/ID.
- Compares required items against `service_items` in the current service plan.
- Renders `✓ Standard DS3 Rubric` or `⚠️ Custom Rubric (X modified)`.

#### Hymn Analytics Foundation
- API endpoint `GET /api/analytics/hymns` returning:
  - Usage count per hymn.
  - Last used date per hymn.
  - Breakdown by liturgical season/day.

---

## 3. Verification & Testing Strategy

- **`tests/test_database.py`**: Validate template table creation, database migration/seeding, and CRUD helper functions.
- **`tests/test_services.py`**: Validate service creation from DB templates, full DS3 ordinary checks, item insertion/replacement logic, and dynamic rubric validation.
- **`tests/test_api.py`**: Test FastAPI endpoints for template management, service CRUD, date updates, and mobile zip exports.
- **Manual Verification**: Test interactive date changing, Services Explorer modal navigation, dual-zone drag-and-drop insertion vs replacement, and template editing in browser.
