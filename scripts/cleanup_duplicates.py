import os
import glob
import re
import argparse
import sys

# Ensure root dir is in sys.path when script is executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.scanner import parse_hymn_file


def find_duplicate_files(directory_path):
    files = glob.glob(os.path.join(directory_path, '*.m4a'))

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

        # Find canonical files (files without ' N.m4a' suffix)
        canonicals = [f for f in file_list if not re.search(r' \d+\.m4a$', os.path.basename(f))]

        if canonicals:
            primary = sorted(canonicals, key=lambda x: (len(os.path.basename(x)), x))[0]
            to_keep.append({'path': primary, 'reason': 'Canonical primary file'})

            for f in file_list:
                if f != primary:
                    to_delete.append({'path': f, 'reason': f'Duplicate of Disc {key[0]} Track {key[1]}'})
        else:
            # Fallback when no canonical file exists
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
    parser.add_argument('--dry-run', action='store_true', help="Run audit in dry-run mode (default)")
    args = parser.parse_args()

    is_dry_run = not args.delete or args.dry_run
    purge_duplicates(args.dir, dry_run=is_dry_run)
