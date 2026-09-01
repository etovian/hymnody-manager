import os
import pytest
from src.database import init_db, save_hymns, search_hymns, get_hymn_by_id, get_db_connection

def test_db_init_and_hymns_crud(tmp_path):
    db_path = str(tmp_path / "test_hymnody.db")
    init_db(db_path)
    
    assert os.path.exists(db_path)
    
    sample_hymns = [
        {
            'hymn_number': 331,
            'title': 'The advent of our King',
            'disc_number': 1,
            'track_number': 1,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\1-01 331 - The advent of our King.m4a',
            'liturgical_season': 'Advent'
        },
        {
            'hymn_number': 332,
            'title': 'Savior of the nations, come',
            'disc_number': 1,
            'track_number': 2,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\1-02 332 - Savior of the nations, come.m4a',
            'liturgical_season': 'Advent'
        }
    ]
    save_hymns(sample_hymns, db_path)
    
    # Test search by title
    results = search_hymns(query="advent", db_path=db_path)
    assert len(results) == 2
    
    # Test search by number
    num_results = search_hymns(query="331", db_path=db_path)
    assert len(num_results) == 1
    assert num_results[0]['hymn_number'] == 331
    
    # Test get_hymn_by_id
    h_id = num_results[0]['id']
    single_hymn = get_hymn_by_id(h_id, db_path=db_path)
    assert single_hymn is not None
    assert single_hymn['title'] == 'The advent of our King'

def test_template_tables_and_service_columns(tmp_path):
    db_path = str(tmp_path / "test_templates_schema.db")
    init_db(db_path)
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_templates'")
        assert cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='template_items'")
        assert cursor.fetchone() is not None
        
        cursor.execute("PRAGMA table_info(services)")
        cols = [col['name'] for col in cursor.fetchall()]
        assert 'liturgical_day' in cols

