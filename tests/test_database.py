import os
import pytest
from src.database import init_db, save_hymns, search_hymns, get_hymn_by_id, get_db_connection, normalize_path


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


def test_search_hymns_by_category_type_and_aliases(tmp_path):
    db_path = str(tmp_path / "test_search_category_alias.db")
    init_db(db_path)
    
    sample_data = [
        {
            'hymn_number': 331,
            'title': 'The advent of our King',
            'disc_number': 1,
            'track_number': 1,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\1-01 331.m4a',
            'liturgical_season': 'Advent'
        },
        {
            'hymn_number': None,
            'title': 'MA - Canticle',
            'disc_number': 30,
            'track_number': 1,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-01 MA.m4a',
            'liturgical_season': 'Matins'
        },
        {
            'hymn_number': None,
            'title': 'VE - Phos Hilaron',
            'disc_number': 30,
            'track_number': 2,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-02 VE.m4a',
            'liturgical_season': 'Vespers'
        },
        {
            'hymn_number': None,
            'title': 'CO - Nunc Dimittis',
            'disc_number': 30,
            'track_number': 3,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-03 CO.m4a',
            'liturgical_season': 'Compline'
        },
        {
            'hymn_number': None,
            'title': 'MP - Venite',
            'disc_number': 30,
            'track_number': 4,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-04 MP.m4a',
            'liturgical_season': 'Morning Prayer'
        },
        {
            'hymn_number': None,
            'title': 'EP - Magnificat',
            'disc_number': 30,
            'track_number': 5,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-05 EP.m4a',
            'liturgical_season': 'Evening Prayer'
        }
    ]
    save_hymns(sample_data, db_path)

    # Test category_type = 'hymn'
    hymns = search_hymns(category_type='hymn', db_path=db_path)
    assert len(hymns) == 1
    assert hymns[0]['hymn_number'] == 331

    # Test category_type = 'liturgy'
    liturgies = search_hymns(category_type='liturgy', db_path=db_path)
    assert len(liturgies) == 5

    # Test aliases
    for alias, season_name in [
        ('matins', 'Matins'), ('ma', 'Matins'),
        ('vespers', 'Vespers'), ('ve', 'Vespers'),
        ('compline', 'Compline'), ('co', 'Compline'),
        ('morning prayer', 'Morning Prayer'), ('mp', 'Morning Prayer'),
        ('evening prayer', 'Evening Prayer'), ('ep', 'Evening Prayer')
    ]:
        res = search_hymns(query=alias, db_path=db_path)
        assert len(res) >= 1, f"Failed for query alias: {alias}"
        assert res[0]['liturgical_season'] == season_name, f"Expected {season_name} for alias {alias}"


def test_path_normalization_and_deduplication(tmp_path):
    db_path = str(tmp_path / "test_norm.db")
    init_db(db_path)

    # 1. Test normalize_path unit function (including forward slashes and drive letters)
    assert normalize_path(r"c:\music\track1.m4a") == r"C:\music\track1.m4a"
    assert normalize_path("c:/music/30-06.m4a") == r"C:\music\30-06.m4a"
    assert normalize_path("") == ""
    assert normalize_path(None) == ""

    # 2. Test direct insertion of mixed-slash and case-differing duplicate paths in DB
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hymns (hymn_number, title, disc_number, track_number, file_path) VALUES (?, ?, ?, ?, ?)",
            (100, "Test Hymn", 1, 1, "c:/music/track1.m4a")
        )
        old_hymn_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO hymns (hymn_number, title, disc_number, track_number, file_path) VALUES (?, ?, ?, ?, ?)",
            (100, "Test Hymn", 1, 1, r"C:\music\track1.m4a")
        )
        new_hymn_id = cursor.lastrowid

        # Insert a service and service_item referencing old_hymn_id
        cursor.execute(
            "INSERT INTO services (service_date, title) VALUES (?, ?)",
            ("2026-09-03", "Test Service")
        )
        service_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path) VALUES (?, ?, ?, ?, ?, ?)",
            (service_id, old_hymn_id, "Test Hymn Item", "Opening Hymn", 1, "c:/music/track1.m4a")
        )
        conn.commit()

    # Verify 2 rows exist in hymns before deduplication
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hymns")
        assert cursor.fetchone()[0] == 2

    # Trigger init_db / deduplication migration
    init_db(db_path)

    # Verify deduplication, path normalization, and foreign key reference preservation
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, file_path FROM hymns")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0]['id'] == new_hymn_id
        assert rows[0]['file_path'] == r"C:\music\track1.m4a"

        # Check service_items updated hymn_id to point to surviving MAX(id) (new_hymn_id)
        cursor.execute("SELECT hymn_id FROM service_items WHERE service_id = ?", (service_id,))
        item = cursor.fetchone()
        assert item['hymn_id'] == new_hymn_id

    # 3. Test save_hymns normalizes file_path automatically
    sample_hymn = {
        'hymn_number': 102,
        'title': 'Another Hymn',
        'disc_number': 1,
        'track_number': 2,
        'file_path': 'c:/music/track2.m4a'
    }
    save_hymns([sample_hymn], db_path)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM hymns WHERE hymn_number = 102")
        row = cursor.fetchone()
        assert row is not None
        assert row['file_path'] == r"C:\music\track2.m4a"




