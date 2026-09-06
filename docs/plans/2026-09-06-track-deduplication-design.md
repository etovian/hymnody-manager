# Design Specification: Track Deduplication & Incremental Ingestion

**Date**: 2026-09-06  
**Status**: Approved  

---

## Executive Summary

Some audio tracks in the `music/` directory exist as duplicate files with numeric suffixes (e.g., `21-19 773 - Hear us, Father, when we pray 1.m4a` through `3.m4a`), caused by past file-system copy operations. When scanned, these files create duplicate database entries in `hymnody.db`. 

This design specification establishes a two-part solution:
1. **App & Database Ingestion Deduplication**: Update `scanner.py` and `database.py` to filter duplicate files by `(disc_number, track_number)` while preserving distinct hymnological settings (such as LSB 536 on Disc 10 Track 20 vs Track 21). Ensure all subsequent scans are incremental and idempotent.
2. **Standalone Cleanup Utility**: Provide `scripts/cleanup_duplicates.py` with strict safety guards so the user can optionally delete redundant suffixed `.m4a` files from disk to reclaim storage.

---

## 1. System Overview & Architecture

### In-App Deduplication (`src/scanner.py` & `src/database.py`)
* **Scanner Filtering**: `scan_hymns_directory()` groups discovered `.m4a` files by `(disc_number, track_number)`. It selects the primary canonical file (preferring shorter, non-suffixed filenames) and ignores suffixed copies (` ... 1.m4a`, ` ... 2.m4a`).
* **Database Migration**: `init_db()` executes an idempotent startup SQL query that cleans up pre-existing duplicate rows in `hymns` sharing the same `(disc_number, track_number)`, retaining only the primary entry.

### Standalone Storage Cleanup Utility (`scripts/cleanup_duplicates.py`)
* A CLI utility for physical disk cleanup, allowing the user to remove redundant suffixed files without violating automated tool read-only restrictions on `/music`.

---

## 2. Retention Rules & Safety Guards

### Track Identity & Categorization
* **Physical Coordinate**: An audio track is uniquely identified by `(disc_number, track_number)`.
* **Canonical Original File**: The file **without** a numeric suffix (e.g. `21-19 773 - Hear us, Father, when we pray.m4a`).
* **Duplicate Candidates**: Files ending with a space and digits before `.m4a` (e.g. `... 1.m4a`, `... 2.m4a`).

### 4-Point Safety Checks (Must ALL pass before file deletion):
1. **Original File Existence**: The canonical file without the ` 1`, ` 2` suffix **MUST exist** in `/music`. If no canonical file exists for a suffixed track, the suffixed file is preserved.
2. **Metadata Match**: Both canonical and suffixed files must parse to the exact same `disc_number` and `track_number`.
3. **Non-Zero File Size**: The canonical original file must have a valid size (> 0 bytes).
4. **Hymnological Protection**: Tracks with different track numbers (e.g., LSB 536 on Disc 10 Track 20 vs Track 21) have distinct track IDs and are never flagged as duplicates.

---

## 3. Incremental Scanning & Idempotency

1. **Existing Track Skip**: `save_hymns()` checks existing database records. If a `(disc_number, track_number)` already exists with a valid canonical file path, secondary/suffixed files found in subsequent scans are skipped.
2. **New Track Insertion**: Unindexed `.m4a` files representing new tracks or discs are inserted normally.
3. **Idempotency**: Running `scan_hymns_directory()` multiple times leaves the database in the exact same clean state.

---

## 4. Testing & Verification Plan

### Automated Pytest Suite (`tests/test_deduplication.py`)
1. **Scanner Test**: Verify `scan_hymns_directory()` filters out suffixed duplicate files while preserving legitimate multi-tune tracks.
2. **Database Migration Test**: Verify `init_db()` deduplicates existing database entries by `(disc_number, track_number)`.
3. **Cleanup Script Safety Test**:
   * Verify suffixed files with matching canonical originals are identified for deletion.
   * Verify suffixed files with missing originals are preserved.
   * Verify `--dry-run` performs zero disk modifications.

### Manual Verification
1. Run `pytest -v` to ensure 100% test pass rate.
2. Run `python scripts/cleanup_duplicates.py --dry-run` to output a full audit of proposed file deletions.
