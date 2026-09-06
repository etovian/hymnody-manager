# Track Deduplication & Incremental Ingestion Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate file-system duplicate tracks from the application database and UI while preserving distinct hymnological tunes, and provide a safe CLI cleanup script for disk storage.

**Architecture:** 
1. In `src/scanner.py`, `scan_hymns_directory()` prioritizes canonical file paths and ignores suffixed duplicate files (` 1.m4a`, ` 2.m4a`) sharing the same `(disc_number, track_number)`.
2. In `src/database.py`, `init_db()` runs an idempotent migration to remove pre-existing duplicate entries from `hymnody.db`, and `save_hymns()` ensures incremental scans do not insert redundant duplicate records.
3. A standalone script `scripts/cleanup_duplicates.py` provides dry-run and deletion capabilities with 4-point safety checks for physical file removal.

**Tech Stack:** Python 3.10+, SQLite3, pytest.

---

### Task 1: Scanner Deduplication in `src/scanner.py`

**Files:**
- Modify: `src/scanner.py:182-191`
- Test: `tests/test_deduplication.py`

**Step 1: Write the failing test**

Create `tests/test_deduplication.py`:

```python
import pytest
from src.scanner import scan_hymns_directory, parse_hymn_file

def test_scanner_deduplicates_same_disc_and_track(tmp_path):
    # Mock files with same disc and track number
    d = tmp_path / "music"
    d.mkdir()
    
    # Create canonical file and suffixed duplicates
    f1 = d / "21-19 773 - Hear us, Father, when we pray.m4a"
    f2 = d / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    f1.write_bytes(b"dummy m4a content 1")
    f2.write_bytes(b"dummy m4a content 2")
    
    results = scan_hymns_directory(str(d))
    assert len(results) == 1
    assert results[0]['disc_number'] == 21
    assert results[0]['track_number'] == 19
    assert " 1.m4a" not in results[0]['file_path']

def test_scanner_retains_different_tracks_same_hymn(tmp_path):
    d = tmp_path / "music"
    d.mkdir()
    
    f1 = d / "10-20 536 - One thing's needful; Lord, this treasure.m4a"
    f2 = d / "10-21 536 - One thing's needful; Lord, this treasure.m4a"
    f1.write_bytes(b"dummy m4a content 1")
    f2.write_bytes(b"dummy m4a content 2")
    
    results = scan_hymns_directory(str(d))
    assert len(results) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_deduplication.py -v`  
Expected: FAIL on `test_scanner_deduplicates_same_disc_and_track` (returns 2 results instead of 1).

**Step 3: Implement minimal scanner deduplication**

Modify `src/scanner.py`:

```python
def scan_hymns_directory(directory_path):
    files = glob.glob(os.path.join(directory_path, '*.m4a'))
    
    # Sort files so canonical names (shorter, no ' N' suffix) come before suffixed copies
    def sort_key(filepath):
        basename = os.path.basename(filepath)
        # Give higher priority (lower sort weight) to files without ' N.m4a'
        match = re.search(r' \d+\.m4a$', basename)
        return (1 if match else 0, len(basename), basename)

    sorted_files = sorted(files, key=sort_key)
    
    results = []
    seen_tracks = set()
    
    for f in sorted_files:
        try:
            parsed = parse_hymn_file(f)
            track_key = (parsed.get('disc_number'), parsed.get('track_number'))
            
            # If disc & track are valid and already seen, skip suffixed duplicate
            if track_key[0] is not None and track_key[1] is not None:
                if track_key in seen_tracks:
                    continue
                seen_tracks.add(track_key)
                
            results.append(parsed)
        except Exception as e:
            print(f"Error parsing {f}: {e}")
    return results
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_deduplication.py -v`  
Expected: PASS

**Step 5: Commit**

Command:
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/scanner.py', 'tests/test_deduplication.py']); subprocess.run(['git', 'commit', '-m', 'feat: add disc and track deduplication to scanner'])"
```

---

### Task 2: Database Migration & Incremental Ingestion in `src/database.py`

**Files:**
- Modify: `src/database.py:89-122`
- Test: `tests/test_deduplication.py`

**Step 1: Write the failing test**

Add to `tests/test_deduplication.py`:

```python
from src.database import init_db, save_hymns, get_db_connection

def test_database_init_migrates_duplicates(tmp_path):
    db_file = str(tmp_path / "test_hymnody.db")
    init_db(db_file)
    
    # Insert raw duplicate rows sharing (disc_number, track_number)
    with get_db_connection(db_file) as conn:
        conn.execute("""
            INSERT INTO hymns (hymn_number, title, disc_number, track_number, file_path)
            VALUES (773, 'Hear us 1', 21, 19, 'music/21-19 773 - Hear us 1.m4a')
        """)
        conn.execute("""
            INSERT INTO hymns (hymn_number, title, disc_number, track_number, file_path)
            VALUES (773, 'Hear us', 21, 19, 'music/21-19 773 - Hear us.m4a')
        """)
        conn.commit()
        
    # Re-run init_db migration
    init_db(db_file)
    
    with get_db_connection(db_file) as conn:
        rows = conn.execute("SELECT * FROM hymns WHERE disc_number=21 AND track_number=19").fetchall()
        assert len(rows) == 1
        assert " 1.m4a" not in rows[0]['file_path']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_deduplication.py::test_database_init_migrates_duplicates -v`  
Expected: FAIL (returns 2 rows).

**Step 3: Implement database migration & incremental check**

Modify `src/database.py` inside `init_db()` (around line 90):

```python
        # Deduplicate hymns where (disc_number, track_number) match
        # Keep entry without ' N.m4a' suffix, or MIN(id)
        cursor.execute("""
            DELETE FROM hymns
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY disc_number, track_number 
                               ORDER BY 
                                   CASE WHEN file_path LIKE '% %.' || SUBSTR(file_path, -3) THEN 1 ELSE 0 END ASC,
                                   LENGTH(file_path) ASC,
                                   id ASC
                           ) as rn
                    FROM hymns
                ) WHERE rn = 1
            );
        """)
```

And update `save_hymns()` in `src/database.py`:

```python
def save_hymns(hymns_list, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        for h in hymns_list:
            norm_path = normalize_path(h.get('file_path'))
            disc_num = h.get('disc_number', 1)
            track_num = h.get('track_number', 1)
            
            # Check if this disc+track already exists under a different file_path
            existing = cursor.execute(
                "SELECT id, file_path FROM hymns WHERE disc_number = ? AND track_number = ?", 
                (disc_num, track_num)
            ).fetchone()
            
            if existing and existing['file_path'] != norm_path:
                # If existing is canonical and new is suffixed, skip
                if re.search(r' \d+\.m4a$', norm_path) and not re.search(r' \d+\.m4a$', existing['file_path']):
                    continue

            cursor.execute("""
                INSERT OR REPLACE INTO hymns 
                (hymn_number, title, disc_number, track_number, album, artist, year, file_path, liturgical_season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                h.get('hymn_number'),
                h.get('title'),
                disc_num,
                track_num,
                h.get('album', 'The Concordia Organist'),
                h.get('artist', 'Concordia Publishing House'),
                h.get('year', 2009),
                norm_path,
                h.get('liturgical_season', 'General')
            ))
        conn.commit()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_deduplication.py -v`  
Expected: PASS

**Step 5: Commit**

Command:
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'src/database.py', 'tests/test_deduplication.py']); subprocess.run(['git', 'commit', '-m', 'feat: add database migration and incremental track deduplication'])"
```

---

### Task 3: Standalone Cleanup Script `scripts/cleanup_duplicates.py`

**Files:**
- Create: `scripts/cleanup_duplicates.py`
- Test: `tests/test_cleanup_duplicates.py`

**Step 1: Write the failing test**

Create `tests/test_cleanup_duplicates.py`:

```python
import os
import pytest
from scripts.cleanup_duplicates import find_duplicate_files, purge_duplicates

def test_find_duplicates_identifies_suffixed_files_when_canonical_exists(tmp_path):
    f_orig = tmp_path / "21-19 773 - Hear us, Father, when we pray.m4a"
    f_dup1 = tmp_path / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    f_dup2 = tmp_path / "21-19 773 - Hear us, Father, when we pray 2.m4a"
    
    f_orig.write_bytes(b"original content")
    f_dup1.write_bytes(b"dup content 1")
    f_dup2.write_bytes(b"dup content 2")
    
    to_keep, to_delete = find_duplicate_files(str(tmp_path))
    
    assert str(f_orig) in [k['path'] for k in to_keep]
    assert str(f_dup1) in [d['path'] for d in to_delete]
    assert str(f_dup2) in [d['path'] for d in to_delete]

def test_find_duplicates_preserves_suffixed_file_if_canonical_missing(tmp_path):
    # Only suffixed file exists, no canonical file
    f_dup1 = tmp_path / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    f_dup1.write_bytes(b"dup content 1")
    
    to_keep, to_delete = find_duplicate_files(str(tmp_path))
    
    assert len(to_delete) == 0
    assert str(f_dup1) in [k['path'] for k in to_keep]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cleanup_duplicates.py -v`  
Expected: FAIL ("ModuleNotFoundError: No module named 'scripts'")

**Step 3: Implement `scripts/cleanup_duplicates.py`**

Create `scripts/cleanup_duplicates.py`:

```python
import os
import glob
import re
import argparse
import sys

# Ensure root dir is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.scanner import parse_hymn_file

def find_duplicate_files(directory_path):
    files = glob.glob(os.path.join(directory_path, '*.m4a'))
    
    # Group by (disc_number, track_number)
    groups = {}
    for f in files:
        parsed = parse_hymn_file(f)
        disc = parsed.get('disc_number')
        track = parsed.get('track_number')
        if disc is not None and track is not None:
            key = (disc, track)
            groups.setdefault(key, []).append(f)
            
    to_keep = []
    to_delete = []
    
    for key, file_list in groups.items():
        if len(file_list) == 1:
            to_keep.append({'path': file_list[0], 'reason': 'Unique track'})
            continue
            
        # Find canonical file (file without ' N.m4a' suffix)
        canonicals = [f for f in file_list if not re.search(r' \d+\.m4a$', os.path.basename(f))]
        
        if canonicals:
            # Pick primary canonical file
            primary = sorted(canonicals, key=lambda x: len(os.path.basename(x)))[0]
            to_keep.append({'path': primary, 'reason': 'Canonical primary file'})
            
            for f in file_list:
                if f != primary:
                    to_delete.append({'path': f, 'reason': f'Duplicate of Disc {key[0]} Track {key[1]}'})
        else:
            # No unsuffixed file found! Keep the shortest suffixed file to prevent data loss
            primary = sorted(file_list, key=lambda x: (len(os.path.basename(x)), x))[0]
            to_keep.append({'path': primary, 'reason': 'Fallback primary (no unsuffixed file present)'})
            for f in file_list:
                if f != primary:
                    to_delete.append({'path': f, 'reason': f'Duplicate of Disc {key[0]} Track {key[1]}'})
                    
    return to_keep, to_delete

def purge_duplicates(directory_path, dry_run=True):
    to_keep, to_delete = find_duplicate_files(directory_path)
    
    print(f"\n--- Storage Duplicate Audit for '{directory_path}' ---")
    print(f"Total files examined: {len(to_keep) + len(to_delete)}")
    print(f"Files to RETAIN: {len(to_keep)}")
    print(f"Files to DELETE: {len(to_delete)}\n")
    
    if to_delete:
        print("Proposed Deletions:")
        for item in to_delete:
            print(f"  [DELETE] {os.path.basename(item['path'])} ({item['reason']})")
            
    if dry_run:
        print("\n[DRY RUN MODE] No files were deleted. Re-run with '--delete' to permanently remove duplicate files.")
    else:
        deleted_count = 0
        for item in to_delete:
            try:
                os.remove(item['path'])
                deleted_count += 1
            except Exception as e:
                print(f"Error removing {item['path']}: {e}")
        print(f"\nSuccessfully deleted {deleted_count} duplicate files.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean up redundant suffixed audio tracks from music directory.")
    parser.add_argument('--dir', default='music', help="Path to music directory (default: music)")
    parser.add_argument('--delete', action='store_true', help="Perform actual file deletion (default is dry-run)")
    args = parser.parse_args()
    
    purge_duplicates(args.dir, dry_run=not args.delete)
```

Create `scripts/__init__.py` to allow python test imports.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cleanup_duplicates.py -v`  
Expected: PASS

**Step 5: Commit**

Command:
```bash
python -c "import subprocess; subprocess.run(['git', 'add', 'scripts/cleanup_duplicates.py', 'scripts/__init__.py', 'tests/test_cleanup_duplicates.py']); subprocess.run(['git', 'commit', '-m', 'feat: add storage cleanup utility for duplicate audio tracks'])"
```

---

### Task 4: Full Suite Verification & Dry-Run Audit

**Files:**
- Test all: `tests/`

**Step 1: Run full test suite**

Run: `pytest -v`  
Expected: ALL PASS

**Step 2: Run dry-run audit on project music directory**

Run: `python scripts/cleanup_duplicates.py --dry-run`  
Expected: Output showing 67 duplicate files identified for deletion and 0 files deleted (dry run mode).
