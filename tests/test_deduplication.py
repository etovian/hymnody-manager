import pytest
from src.scanner import scan_hymns_directory
from src.database import init_db, save_hymns, get_db_connection

def test_scanner_deduplicates_same_disc_and_track(tmp_path):
    canonical = tmp_path / "21-19 773 - Hear us, Father, when we pray.m4a"
    suffixed = tmp_path / "21-19 773 - Hear us, Father, when we pray 1.m4a"
    
    canonical.touch()
    suffixed.touch()
    
    results = scan_hymns_directory(str(tmp_path))
    assert len(results) == 1
    assert results[0]['filename'] == "21-19 773 - Hear us, Father, when we pray.m4a"

def test_scanner_retains_different_tracks_same_hymn(tmp_path):
    track1 = tmp_path / "10-20 500 - Creator Spirit, by whose aid.m4a"
    track2 = tmp_path / "10-21 500 - Creator Spirit, by whose aid.m4a"
    
    track1.touch()
    track2.touch()
    
    results = scan_hymns_directory(str(tmp_path))
    assert len(results) == 2

def test_scanner_preserves_unnumbered_files(tmp_path):
    file1 = tmp_path / "DS1_Kyrie.m4a"
    file2 = tmp_path / "DS1_Gloria.m4a"
    
    file1.touch()
    file2.touch()
    
    results = scan_hymns_directory(str(tmp_path))
    assert len(results) == 2
    filenames = [r['filename'] for r in results]
    assert "DS1_Kyrie.m4a" in filenames
    assert "DS1_Gloria.m4a" in filenames

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

def test_save_hymns_skips_duplicate_suffixed_tracks(tmp_path):
    db_file = str(tmp_path / "test_hymnody.db")
    init_db(db_file)
    
    canonical_hymn = {
        'hymn_number': 773,
        'title': 'Hear us',
        'disc_number': 21,
        'track_number': 19,
        'file_path': 'music/21-19 773 - Hear us.m4a',
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'liturgical_season': 'General'
    }
    
    suffixed_hymn = {
        'hymn_number': 773,
        'title': 'Hear us 1',
        'disc_number': 21,
        'track_number': 19,
        'file_path': 'music/21-19 773 - Hear us 1.m4a',
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'liturgical_season': 'General'
    }
    
    save_hymns([canonical_hymn, suffixed_hymn], db_file)
    
    with get_db_connection(db_file) as conn:
        rows = conn.execute("SELECT * FROM hymns WHERE disc_number=21 AND track_number=19").fetchall()
        assert len(rows) == 1
        assert " 1.m4a" not in rows[0]['file_path']


