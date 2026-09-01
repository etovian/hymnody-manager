import io
import zipfile
import pytest
from src.database import init_db, save_hymns
from src.services import create_service_from_preset, get_service_details, update_service_items
from src.exporter import export_service_zip

def test_export_service_zip(tmp_path):
    db_path = str(tmp_path / "export_test.db")
    init_db(db_path)
    
    sample_file = r'c:\dev\IdeaProjects\hymnody-manager\music\1-01 331 - The advent of our King.m4a'
    save_hymns([{
        'hymn_number': 331,
        'title': 'The advent of our King',
        'disc_number': 1,
        'track_number': 1,
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'file_path': sample_file,
        'liturgical_season': 'Advent'
    }], db_path)
    
    srv_id = create_service_from_preset("Test Service", "2026-08-30", "DS2", db_path=db_path)
    details = get_service_details(srv_id, db_path=db_path)
    items = details['items']
    items[0]['file_path'] = sample_file
    items[0]['item_title'] = "The advent of our King"
    update_service_items(srv_id, items, db_path=db_path)
    
    zip_bytes = export_service_zip(srv_id, db_path=db_path)
    assert zip_bytes is not None
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "playlist.m3u" in names
        assert any(n.endswith(".m4a") for n in names)
        
        m3u_content = zf.read("playlist.m3u").decode("utf-8")
        assert "#EXTM3U" in m3u_content

def test_export_service_zip_preserves_track_numbering_for_missing_files(tmp_path):
    db_path = str(tmp_path / "test_export_seq.db")
    init_db(db_path)
    
    sample_hymn = tmp_path / "1-01 331 - Test Hymn.m4a"
    sample_hymn.write_bytes(b"dummy m4a content")
    
    hymns = [
        {'id': 1, 'hymn_number': 331, 'title': 'Test Hymn 1', 'disc_number': 1, 'track_number': 1, 'file_path': str(sample_hymn), 'liturgical_season': 'General'},
        {'id': 2, 'hymn_number': 332, 'title': 'Test Hymn 3', 'disc_number': 1, 'track_number': 2, 'file_path': str(sample_hymn), 'liturgical_season': 'General'}
    ]
    save_hymns(hymns, db_path=db_path)
    
    from src.database import get_db_connection
    items = [
        {'hymn_id': 1, 'slot_name': 'Opening Hymn', 'item_title': 'Test Hymn 1', 'sequence_order': 1, 'file_path': str(sample_hymn)},
        {'hymn_id': None, 'slot_name': 'Venite', 'item_title': 'Venite (O Come)', 'sequence_order': 2, 'file_path': ''},
        {'hymn_id': 2, 'slot_name': 'Office Hymn', 'item_title': 'Test Hymn 3', 'sequence_order': 3, 'file_path': str(sample_hymn)}
    ]
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (service_date, title, setting_preset) VALUES ('2026-09-01', 'Test Matins', 'Matins')")
        s_id = cursor.lastrowid
        for it in items:
            cursor.execute("""
                INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (s_id, it['hymn_id'], it['item_title'], it['slot_name'], it['sequence_order'], it['file_path']))
        conn.commit()
        
    zip_bytes = export_service_zip(s_id, db_path=db_path)
    assert zip_bytes is not None
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        namelist = zf.namelist()
        assert "01_Opening_Hymn_Test_Hymn_1.m4a" in namelist
        assert "03_Office_Hymn_Test_Hymn_3.m4a" in namelist
        assert "02_Venite_Venite_(O_Come).m4a" not in namelist
        
        m3u_content = zf.read("playlist.m3u").decode('utf-8')
        assert "01_Opening_Hymn_Test_Hymn_1.m4a" in m3u_content
        assert "03_Office_Hymn_Test_Hymn_3.m4a" in m3u_content

