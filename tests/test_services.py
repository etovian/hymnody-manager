import os
import pytest
from src.database import init_db, save_hymns
from src.services import create_service_from_preset, get_service_details, update_service_items

def test_create_service_ds2_preset(tmp_path):
    db_path = str(tmp_path / "services_test.db")
    init_db(db_path)
    
    # Pre-populate dummy canticle tracks into DB
    save_hymns([
        {
            'hymn_number': None,
            'title': 'DS2 - Kyrie_ Intonation',
            'disc_number': 30,
            'track_number': 30,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-30 DS2 - Kyrie_ Intonation.m4a',
            'liturgical_season': 'Liturgical'
        },
        {
            'hymn_number': None,
            'title': 'DS2 - Gloria in Excelsis',
            'disc_number': 30,
            'track_number': 31,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\30-31 DS2 - Gloria in Excelsis.m4a',
            'liturgical_season': 'Liturgical'
        }
    ], db_path)
    
    service_id = create_service_from_preset(
        title="1st Sunday in Advent",
        service_date="2026-11-29",
        setting_preset="DS2",
        liturgical_color="Blue",
        db_path=db_path
    )
    
    assert service_id is not None
    details = get_service_details(service_id, db_path=db_path)
    assert details['title'] == "1st Sunday in Advent"
    assert len(details['items']) > 0
    
    # Check that Kyrie canticle matched correctly
    kyrie_item = next((item for item in details['items'] if "Kyrie" in item['slot_name']), None)
    assert kyrie_item is not None
    assert "DS2" in kyrie_item['item_title']

def test_update_service_items(tmp_path):
    db_path = str(tmp_path / "services_update_test.db")
    init_db(db_path)
    
    service_id = create_service_from_preset(
        title="Test Service",
        service_date="2026-11-29",
        setting_preset="DS2",
        db_path=db_path
    )
    
    details = get_service_details(service_id, db_path=db_path)
    items = details['items']
    
    # Assign a hymn to Opening Hymn slot
    items[0]['hymn_id'] = 1
    items[0]['item_title'] = "LSB 331 - The advent of our King"
    items[0]['file_path'] = r"c:\dev\IdeaProjects\hymnody-manager\music\1-01 331 - The advent of our King.m4a"
    
    update_service_items(service_id, items, db_path=db_path)
    
    updated_details = get_service_details(service_id, db_path=db_path)
    assert updated_details['items'][0]['hymn_id'] == 1
    assert updated_details['items'][0]['item_title'] == "LSB 331 - The advent of our King"
