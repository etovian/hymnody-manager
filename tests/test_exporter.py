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
