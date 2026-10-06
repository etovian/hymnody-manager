# Track Info Modal Enhancements Design

## 1. Overview
This design enhances the Track Info Modal (Hymn Details Modal) in the Hymnody Manager web application. As hymns are scheduled and used in worship services over time, the "Previous Service Usage" section needs to support vertical scrolling without pushing the rest of the modal offscreen. Additionally, the table layout is refined by removing the redundant "Service Title" column, renaming the section to "Service Usage" (to embrace both past and future scheduled uses), and introducing a humanized relative time column ("When") that computes elapsed time for past services or remaining time for upcoming services.

---

## 2. Goals & Key Requirements
1. **Vertical Scrolling & Sticky Headers**: Constrain `#modal-history-container` to `max-height: 220px` (showing ~5–6 rows) with `overflow-y: auto`, while keeping the table header (`<thead> th`) sticky at `top: 0` so column labels remain visible during scrolling.
2. **Column Streamlining**:
   - Remove the `Service Title` column. Liturgical Day provides sufficient and clearer identification of the service occasion.
   - Insert a new `When` column immediately adjacent to `Date`.
   - Resulting table columns: `Date`, `When`, `Liturgical Day`, `Setting`, `Slot`.
3. **Relative Time Formatting ("When")**:
   - Compare service date (`YYYY-MM-DD`) against current calendar date (using midnight-normalized local calendar dates).
   - Same-day (\(\Delta d = 0\)): `"Today"`
   - Immediate past/future: \(-1\) \(\rightarrow\) `"Yesterday"`, \(+1\) \(\rightarrow\) `"Tomorrow"`
   - Recent past (\(-2\) to \(-13\) days): `"${n} days ago"`
   - Weeks past (\(-14\) to \(-59\) days): `"${Math.round(n / 7)} weeks ago"`
   - Months past (\(\le -60\) days): `"${Math.round(n / 30)} months ago"`
   - Upcoming in days (\(+2\) to \(+13\) days): `"In ${n} days"`
   - Upcoming in weeks (\(+14\) to \(+59\) days): `"In ${Math.round(n / 7)} weeks"`
   - Upcoming in months (\(\ge +60\) days): `"In ${Math.round(n / 30)} months"`
   - Invalid / empty dates: `"-"`
4. **Visual Accent for Upcoming Services**:
   - Future entries in the `When` column render with a subtle cyan/sky blue text accent (`#38bdf8`) with font-weight `500`.
   - Past entries and same-day entries render in standard muted slate (`#94a3b8` / `#cbd5e1`).
5. **Section Heading Update**:
   - Update heading text from `"Previous Service Usage"` to `"Service Usage"` (and dynamic title `"Service Usage (${count})"`).

---

## 3. Architecture & UI Changes

### 3.1 HTML & CSS Structure (`src/static/index.html` & `src/static/styles.css`)
- **HTML (`src/static/index.html`)**:
  - Update `#modal-history-heading` text to `"Service Usage"`.
- **CSS (`src/static/styles.css`)**:
  - Add `#modal-history-container` styling:
    ```css
    #modal-history-container {
      max-height: 220px;
      overflow-y: auto;
      overflow-x: auto;
    }
    ```
  - Enhance `.hymn-history-table th`:
    ```css
    .hymn-history-table th {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #1e293b;
      /* existing padding, font styles retained */
    }
    ```
  - Add style class for relative time accents:
    ```css
    .history-when-upcoming {
      color: #38bdf8;
      font-weight: 500;
    }
    .history-when-past {
      color: #94a3b8;
    }
    ```

### 3.2 Frontend Logic (`src/static/app.js`)
1. **Helper Function `formatRelativeServiceDate(dateStr, now = new Date())`**:
   - Parses `dateStr` as local `YYYY-MM-DD` (e.g. `new Date(year, month - 1, day)`).
   - Computes whole day difference: `Math.round((serviceDate - todayMidnight) / (1000 * 60 * 60 * 24))`.
   - Returns `{ text: string, isUpcoming: boolean }`.
2. **Modal Population (`openHymnDetailsModal`)**:
   - Set `historyHeading.textContent = `Service Usage (${usageHistory.length})``.
   - Construct table headers: `Date`, `When`, `Liturgical Day`, `Setting`, `Slot`.
   - Map `usageHistory` rows without `service_title`, injecting formatted relative time into the `When` cell.

---

## 4. Testing & Verification

1. **Unit Tests**:
   - Test `formatRelativeServiceDate` helper logic across boundary conditions:
     - Delta = 0 ("Today")
     - Delta = -1 ("Yesterday") / +1 ("Tomorrow")
     - Delta = -7 ("1 week ago" or "7 days ago" depending on threshold; 7 days -> "1 week ago")
     - Delta = -14 ("2 weeks ago"), -35 ("5 weeks ago")
     - Delta = -60 ("2 months ago"), -180 ("6 months ago")
     - Delta = +5 ("In 5 days"), +21 ("In 3 weeks"), +90 ("In 3 months")
     - Null, empty string, or malformed input -> `"-"`
2. **Regression & Integration Tests**:
   - Run `python -m pytest tests/` to confirm all 92 existing tests pass cleanly.
3. **Manual / Browser Verification**:
   - Open track info modal on a track with no usage history -> verify clean empty state.
   - Open modal on a track with multiple service usages -> verify:
     - 5 columns (`Date`, `When`, `Liturgical Day`, `Setting`, `Slot`).
     - Scrolling activates when more than 5 rows are present, and column header sticks to top.
     - Relative time text matches expectations for past and upcoming service dates with proper cyan accent for future dates.
