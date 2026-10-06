# Track Info Modal Enhancements Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the Track Info Modal by making the service usage history table scrollable with sticky headers, removing the redundant Service Title column, and adding a relative time ("When") column that computes elapsed or upcoming time with color accents.

**Architecture:** Update HTML and CSS to constrain `#modal-history-container` to `max-height: 220px` with sticky `th` elements. Add a modular date helper `formatRelativeServiceDate` in `src/static/app.js` with comprehensive edge-case handling, and wire it into the modal rendering logic to replace the `Service Title` column with `When` and display formatted relative durations.

**Tech Stack:** Vanilla JavaScript (ES6+), CSS3 (Flexbox, sticky positioning), HTML5, Python 3.11 / Pytest (FastAPI, BeautifulSoup/E2E test suite).

---

### Task 1: CSS and HTML Structure for Scrollable Container and Sticky Header

**Files:**
- Modify: `src/static/index.html:310-317`
- Modify: `src/static/styles.css:844-865`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**
In `tests/test_e2e.py`, add a test verifying the new heading text, container scroll styles, and sticky table header in CSS.

```python
def test_hymn_details_modal_history_scrolling_and_heading():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    # Verify heading is "Service Usage" instead of "Previous Service Usage"
    assert '<h4 id="modal-history-heading"' in html
    assert "Service Usage" in html
    assert "Previous Service Usage" not in html

    # Verify container has max-height and overflow styles in CSS
    assert "#modal-history-container" in css
    assert "max-height: 220px;" in css
    assert "overflow-y: auto;" in css

    # Verify table headers are sticky with background in CSS
    assert "position: sticky;" in css
    assert "top: 0;" in css
    assert "z-index:" in css
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py -k test_hymn_details_modal_history_scrolling_and_heading -v`
Expected: FAIL (assertion error for CSS / HTML differences)

**Step 3: Implement HTML and CSS changes**
In `src/static/index.html`:
Update `#modal-history-heading` text to `"Service Usage"`.

In `src/static/styles.css`:
Add styles for `#modal-history-container`:
```css
#modal-history-container {
  max-height: 220px;
  overflow-y: auto;
  overflow-x: auto;
}
```
Update `.hymn-history-table th`:
```css
.hymn-history-table th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #1e293b;
  color: #94a3b8;
  font-weight: 600;
  padding: 8px 12px;
  border-bottom: 1px solid #334155;
}
```
Add relative time accent classes:
```css
.history-when-upcoming {
  color: #38bdf8;
  font-weight: 500;
}
.history-when-past {
  color: #94a3b8;
}
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py -k test_hymn_details_modal_history_scrolling_and_heading -v`
Expected: PASS

**Step 5: Commit changes**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/index.html', 'src/static/styles.css', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'feat: add scrollable container, sticky header, and rename heading to Service Usage'])"
```

---

### Task 2: Relative Date Calculation Function (`formatRelativeServiceDate`)

**Files:**
- Modify: `src/static/app.js`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**
In `tests/test_e2e.py`, add a test executing `formatRelativeServiceDate` via Node.js or evaluating its exports against all boundary conditions:
- Same-day (\(\Delta d = 0\)) \(\rightarrow\) `"Today"`
- Yesterday (\(\Delta d = -1\)) \(\rightarrow\) `"Yesterday"`
- Tomorrow (\(\Delta d = +1\)) \(\rightarrow\) `"Tomorrow"`
- Past in days: \(-5\) \(\rightarrow\) `"5 days ago"`, \(-13\) \(\rightarrow\) `"13 days ago"`
- Past in weeks: \(-14\) \(\rightarrow\) `"2 weeks ago"`, \(-35\) \(\rightarrow\) `"5 weeks ago"`
- Past in months: \(-60\) \(\rightarrow\) `"2 months ago"`, \(-180\) \(\rightarrow\) `"6 months ago"`
- Future in days: \(+5\) \(\rightarrow\) `"In 5 days"`, \(+13\) \(\rightarrow\) `"In 13 days"`
- Future in weeks: \(+14\) \(\rightarrow\) `"In 2 weeks"`, \(+35\) \(\rightarrow\) `"In 5 weeks"`
- Future in months: \(+60\) \(\rightarrow\) `"In 2 months"`, \(+180\) \(\rightarrow\) `"In 6 months"`
- Invalid / missing: `null`, `""`, `"invalid"` \(\rightarrow\) text `"-"`, `isUpcoming: false`

```python
def test_format_relative_service_date_logic():
    import subprocess, json
    # Run a node snippet that extracts formatRelativeServiceDate from app.js and runs assertions
    node_script = """
    const fs = require('fs');
    const code = fs.readFileSync('src/static/app.js', 'utf-8');
    // Extract formatRelativeServiceDate function
    const fnMatch = code.match(/function formatRelativeServiceDate[\\s\\S]*?\\n}/);
    if (!fnMatch) {
        console.error("Function formatRelativeServiceDate not found in app.js");
        process.exit(1);
    }
    eval(fnMatch[0]);

    const refDate = new Date(2026, 9, 6); // 2026-10-06
    const cases = [
        { date: '2026-10-06', expectedText: 'Today', upcoming: false },
        { date: '2026-10-05', expectedText: 'Yesterday', upcoming: false },
        { date: '2026-10-07', expectedText: 'Tomorrow', upcoming: true },
        { date: '2026-10-01', expectedText: '5 days ago', upcoming: false },
        { date: '2026-09-23', expectedText: '13 days ago', upcoming: false },
        { date: '2026-09-22', expectedText: '2 weeks ago', upcoming: false },
        { date: '2026-08-07', expectedText: '2 months ago', upcoming: false },
        { date: '2026-10-11', expectedText: 'In 5 days', upcoming: true },
        { date: '2026-10-19', expectedText: 'In 13 days', upcoming: true },
        { date: '2026-10-20', expectedText: 'In 2 weeks', upcoming: true },
        { date: '2026-12-05', expectedText: 'In 2 months', upcoming: true },
        { date: null, expectedText: '-', upcoming: false },
        { date: '', expectedText: '-', upcoming: false },
        { date: 'invalid-date', expectedText: '-', upcoming: false },
    ];

    for (const c of cases) {
        const res = formatRelativeServiceDate(c.date, refDate);
        if (res.text !== c.expectedText || res.isUpcoming !== c.upcoming) {
            console.error(`Mismatch for ${c.date}: expected ${c.expectedText} (upcoming: ${c.upcoming}), got ${res.text} (upcoming: ${res.isUpcoming})`);
            process.exit(1);
        }
    }
    console.log("ALL_PASSED");
    """
    res = subprocess.run(["node", "-e", node_script], capture_output=True, text=True)
    assert res.returncode == 0, f"Node test failed: {res.stderr}\n{res.stdout}"
    assert "ALL_PASSED" in res.stdout
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py -k test_format_relative_service_date_logic -v`
Expected: FAIL (Function formatRelativeServiceDate not found)

**Step 3: Implement `formatRelativeServiceDate` in `src/static/app.js`**
Add the function in `src/static/app.js`:
```javascript
function formatRelativeServiceDate(serviceDateStr, now = new Date()) {
  if (!serviceDateStr || typeof serviceDateStr !== 'string') {
    return { text: '-', isUpcoming: false };
  }
  const parts = serviceDateStr.trim().split('-');
  if (parts.length !== 3) {
    return { text: '-', isUpcoming: false };
  }
  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);
  if (isNaN(year) || isNaN(month) || isNaN(day)) {
    return { text: '-', isUpcoming: false };
  }

  const targetDate = new Date(year, month, day);
  if (isNaN(targetDate.getTime())) {
    return { text: '-', isUpcoming: false };
  }

  const todayMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffMs = targetDate.getTime() - todayMidnight.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return { text: 'Today', isUpcoming: false };
  }
  if (diffDays === 1) {
    return { text: 'Tomorrow', isUpcoming: true };
  }
  if (diffDays === -1) {
    return { text: 'Yesterday', isUpcoming: false };
  }

  if (diffDays > 1) {
    if (diffDays <= 13) {
      return { text: `In ${diffDays} days`, isUpcoming: true };
    }
    const weeks = Math.round(diffDays / 7);
    if (diffDays < 60) {
      return { text: `In ${weeks} weeks`, isUpcoming: true };
    }
    const months = Math.round(diffDays / 30);
    return { text: `In ${months} months`, isUpcoming: true };
  } else {
    const absDays = Math.abs(diffDays);
    if (absDays <= 13) {
      return { text: `${absDays} days ago`, isUpcoming: false };
    }
    const weeks = Math.round(absDays / 7);
    if (absDays < 60) {
      return { text: `${weeks} weeks ago`, isUpcoming: false };
    }
    const months = Math.round(absDays / 30);
    return { text: `${months} months ago`, isUpcoming: false };
  }
}
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e.py -k test_format_relative_service_date_logic -v`
Expected: PASS

**Step 5: Commit changes**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'feat: add formatRelativeServiceDate helper with tests'])"
```

---

### Task 3: Integrate Table Columns, When Column Accent, and Update Heading in Modal Workflow

**Files:**
- Modify: `src/static/app.js:295, 350-385`
- Test: `tests/test_e2e.py`

**Step 1: Write the failing test**
In `tests/test_e2e.py`, update `test_hymn_details_modal_ui_and_js_logic` and `test_hymn_details_modal_workflow_e2e` to verify:
1. `historyHeading` displays `"Service Usage"` instead of `"Previous Service Usage"`.
2. The history table headers contain `<th>Date</th>`, `<th>When</th>`, `<th>Liturgical Day</th>`, `<th>Setting</th>`, `<th>Slot</th>`, and DO NOT contain `<th>Service Title</th>`.
3. The rendered row contains the `When` cell with class `history-when-upcoming` or `history-when-past`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e.py -k test_hymn_details_modal -v`
Expected: FAIL

**Step 3: Implement modal rendering updates in `src/static/app.js`**
1. At line 295: Update default text from `'Previous Service Usage'` to `'Service Usage'`.
2. At line 352: Update dynamic heading to `historyHeading.textContent = \`Service Usage (\${usageHistory.length})\``.
3. At lines 358–384:
   - Format relative date using `formatRelativeServiceDate(u.service_date)`.
   - Render rows with 5 columns:
     ```javascript
     const rel = formatRelativeServiceDate(u.service_date);
     const whenClass = rel.isUpcoming ? 'history-when-upcoming' : 'history-when-past';
     return `
       <tr>
         <td>${escapeHtml(u.service_date || '-')}</td>
         <td class="${whenClass}">${escapeHtml(rel.text)}</td>
         <td>${escapeHtml(u.liturgical_day || '-')}</td>
         <td>${escapeHtml(u.setting_preset || '-')}</td>
         <td>${escapeHtml(u.slot_name || '-')}</td>
       </tr>
     `;
     ```
   - Render table header:
     ```html
     <thead>
       <tr>
         <th>Date</th>
         <th>When</th>
         <th>Liturgical Day</th>
         <th>Setting</th>
         <th>Slot</th>
       </tr>
     </thead>
     ```

**Step 4: Run full test suite to verify everything passes**

Run: `python -m pytest -v`
Expected: All tests PASS with zero regressions.

**Step 5: Commit changes**

```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/static/app.js', 'tests/test_e2e.py']); subprocess.run(['git', 'commit', '-m', 'feat: update modal table to 5 columns with When relative time and Service Usage heading'])"
```

---

## Verification Checklist
- [ ] Table container `#modal-history-container` has `max-height: 220px` and scrolls vertically when more than 5 items exist.
- [ ] Table headers (`thead th`) stick to top while scrolling.
- [ ] `Service Title` column is removed.
- [ ] `When` column is positioned directly adjacent to `Date`.
- [ ] Relative time displays correctly ("Today", "Yesterday", "Tomorrow", "X days ago / In X days", "X weeks ago / In X weeks", "X months ago / In X months").
- [ ] Upcoming service dates have cyan accent (`#38bdf8`, medium weight).
- [ ] Heading displays "Service Usage" and dynamic count "Service Usage (N)".
- [ ] Full automated test suite passes (`python -m pytest -v`).
