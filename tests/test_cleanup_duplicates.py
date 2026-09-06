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
    f_dup1 = tmp_path / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    f_dup1.write_bytes(b"dup content 1")

    to_keep, to_delete = find_duplicate_files(str(tmp_path))

    assert len(to_delete) == 0
    assert str(f_dup1) in [k['path'] for k in to_keep]


def test_purge_duplicates_dry_run_mode(tmp_path):
    f_orig = tmp_path / "21-19 773 - Hear us, Father, when we pray.m4a"
    f_dup1 = tmp_path / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    f_dup2 = tmp_path / "21-19 773 - Hear us, Father, when we pray 2.m4a"

    f_orig.write_bytes(b"original content")
    f_dup1.write_bytes(b"dup content 1")
    f_dup2.write_bytes(b"dup content 2")

    purge_duplicates(str(tmp_path), dry_run=True)

    assert f_orig.exists()
    assert f_dup1.exists()
    assert f_dup2.exists()


def test_purge_duplicates_delete_mode(tmp_path):
    f_orig = tmp_path / "21-19 773 - Hear us, Father, when we pray.m4a"
    f_dup1 = tmp_path / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    f_dup2 = tmp_path / "21-19 773 - Hear us, Father, when we pray 2.m4a"

    f_orig.write_bytes(b"original content")
    f_dup1.write_bytes(b"dup content 1")
    f_dup2.write_bytes(b"dup content 2")

    purge_duplicates(str(tmp_path), dry_run=False)

    assert f_orig.exists()
    assert not f_dup1.exists()
    assert not f_dup2.exists()
