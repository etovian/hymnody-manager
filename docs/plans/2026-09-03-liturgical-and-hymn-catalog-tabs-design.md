# Design Specification: Dual-Tab Hymnal Catalog & Liturgical Categorization

**Date**: 2026-09-03  
**Status**: Approved  

---

## 1. Overview

The Hymnal Catalog panel currently presents a single flat list of audio tracks with basic season filters. This design upgrades the catalog into a two-tab interface separating **Hymns** (LSB 331–982) from **Liturgy & Canticles** (Divine Services DS1–DS5 and Daily Office settings Matins, Vespers, Morning Prayer, Evening Prayer, Compline, Psalm Tones).

Additionally, this spec updates the audio scanning and metadata classification engine to correctly categorize all 86 tracks on Disc 31 (Matins, Vespers, etc.) and expands topical categories to include **Holy Communion / Lord's Supper**, **Holy Baptism**, **Confession & Absolution**, and other LSB sections.

---

## 2. Key Architecture & Features

### 2.1 Dual-Tab Catalog Interface (`src/static/index.html` & `app.js`)
- **[🎵 Hymns] Tab**:
  - Displays congregational hymns from Discs 1–29.
  - **Filter Pills**: `All` | `Advent` | `Christmas` | `Epiphany` | `Lent` | `Easter` | `Pentecost` | `Communion` | `Baptism` | `Trust & Comfort` | `Praise` | `General`.
  - Default sort: LSB Hymn Number ASC.
- **[📜 Liturgy] Tab**:
  - Displays liturgical ordinaries, canticles, and daily office settings from Discs 30 & 31.
  - **Filter Pills**: `All Services` | `DS1` | `DS2` | `DS3` | `DS4` | `DS5` | `Matins` | `Vespers` | `Morning Prayer` | `Evening Prayer` | `Compline` | `Psalm Tones`.
  - Default sort: Disc & Track Number ASC.

### 2.2 Audio Scanning & Category Classification (`src/scanner.py`)
- **Disc 30 (Divine Service Settings)**:
  - Tracks 30-01 to 30-29: `DS1`
  - Tracks 30-30 to 30-58: `DS2`
  - Tracks 30-59 to 30-82: `DS3`
  - Tracks 30-83 to 30-90: `DS4`
  - Tracks 30-91 to 30-96: `DS5`
- **Disc 31 (Daily Office & Canticles)**:
  - Tracks 31-01 to 31-18 (`MA - ...`): `Matins`
  - Tracks 31-19 to 31-34 (`VE - ...`): `Vespers`
  - Tracks 31-35 to 31-45 (`MP - ...`): `Morning Prayer`
  - Tracks 31-46 to 31-59 (`EP - ...`): `Evening Prayer`
  - Tracks 31-60 to 31-73 (`CO - ...`): `Compline`
  - Tracks 31-74 to 31-86 (`PP - ...`, `PT - ...`): `Psalm Tones`
- **Discs 1–29 (Hymn Index Ranges)**:
  - LSB 331–357: `Advent`
  - LSB 358–393: `Christmas`
  - LSB 394–417: `Epiphany`
  - LSB 418–456: `Lent`
  - LSB 457–490: `Easter`
  - LSB 491–503: `Pentecost`
  - LSB 590–605: `Baptism`
  - LSB 606–616: `Confession`
  - LSB 617–643: `Communion`
  - LSB 708–780: `Trust & Comfort`
  - LSB 781–824: `Praise`
  - LSB 504–589 & 644–707 & 825–982: `General` (or specific subtopic)

### 2.3 Search & Database Querying (`src/database.py`)
- `search_hymns(query=None, season=None, category_type=None, disc=None)`:
  - `category_type='hymn'`: Returns only items with a non-null `hymn_number` (Discs 1–29).
  - `category_type='liturgy'`: Returns only items from Discs 30 & 31.
  - Keyword search in `query`: Matches titles, hymn numbers, liturgical seasons, and setting abbreviations (e.g. typing `"matins"` or `"te deum"` returns Matins tracks).

---

## 3. Data Flow & UI State Management

1. **User clicks [🎵 Hymns] tab**:
   - `activeCatalogTab` set to `'hymn'`.
   - Category filter pills update to show Church Year & Topical seasons.
   - `fetchHymns()` passes `category_type=hymn`.
2. **User clicks [📜 Liturgy] tab**:
   - `activeCatalogTab` set to `'liturgy'`.
   - Category filter pills update to show Orders of Service (`DS1`..`DS5`, `Matins`, `Vespers`, `Morning Prayer`, `Evening Prayer`, `Compline`, `Psalm Tones`).
   - `fetchHymns()` passes `category_type=liturgy`.
3. **User types in search box**:
   - Query filters within the active tab.

---

## 4. Verification Plan

### Automated Unit & API Tests
- `tests/test_scanner.py`: Test scanner correctly tags Matins (`MA -`), Vespers (`VE -`), DS1–DS5, Communion (617–643), Baptism (590–605), etc.
- `tests/test_database.py`: Test `search_hymns()` filtering by `category_type='hymn'` vs `category_type='liturgy'`, as well as by specific order of service or season.
- `tests/test_api.py`: Test `GET /api/hymns?category_type=liturgy&season=Matins` returns all 18 Matins tracks.
