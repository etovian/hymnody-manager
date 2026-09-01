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

def test_seed_templates_and_corrected_ds3(tmp_path):
    from src.services import seed_templates_if_empty, list_templates, get_template_by_name, update_service_metadata
    db_path = str(tmp_path / "templates_test.db")
    init_db(db_path)
    seed_templates_if_empty(db_path)
    
    templates = list_templates(db_path)
    assert len(templates) >= 7
    
    ds3 = get_template_by_name("DS3", db_path)
    assert ds3 is not None
    
    items = ds3['items']
    salutation = next((i for i in items if "Salutation" in i['item_title'] or "Salutation" in i['slot_name']), None)
    assert salutation is not None
    
    collect_amen = next((i for i in items if "Amen" in i['item_title'] or "Amen" in i['slot_name']), None)
    assert collect_amen is not None
    
    # Check that DS1 through DS5 templates have two distribution slots
    for setting in ["DS1", "DS2", "DS3", "DS4", "DS5"]:
        tmpl = get_template_by_name(setting, db_path)
        t_items = tmpl['items']
        dist1 = next((i for i in t_items if "Distribution 1" in i['slot_name'] or "Distribution Hymn 1" in i['item_title']), None)
        dist2 = next((i for i in t_items if "Distribution 2" in i['slot_name'] or "Distribution Hymn 2" in i['item_title']), None)
        assert dist1 is not None, f"Missing Distribution 1 in {setting}"
        assert dist2 is not None, f"Missing Distribution 2 in {setting}"


def test_update_service_metadata(tmp_path):
    from src.services import update_service_metadata
    db_path = str(tmp_path / "metadata_test.db")
    init_db(db_path)
    
    service_id = create_service_from_preset(
        title="Original Service",
        service_date="2026-09-01",
        setting_preset="DS3",
        db_path=db_path
    )
    
    update_service_metadata(
        service_id=service_id,
        service_date="2026-09-06",
        liturgical_day="15th Sunday after Trinity",
        title="Trinity Worship",
        notes="Guest organist",
        db_path=db_path
    )
    
    details = get_service_details(service_id, db_path=db_path)
    assert details['service_date'] == "2026-09-06"
    assert details['liturgical_day'] == "15th Sunday after Trinity"
    assert details['title'] == "Trinity Worship"
    assert details['notes'] == "Guest organist"

def test_hymn_slots_are_placeholders_without_default_hymns(tmp_path):
    db_path = str(tmp_path / "placeholder_test.db")
    init_db(db_path)
    
    for setting in ["DS1", "DS2", "DS3", "DS4", "DS5", "Matins", "Vespers"]:
        service_id = create_service_from_preset(
            title=f"Test {setting}",
            service_date="2026-09-01",
            setting_preset=setting,
            db_path=db_path
        )
        details = get_service_details(service_id, db_path=db_path)
        for item in details['items']:
            if "hymn" in item['slot_name'].lower() or "hymn" in item['item_title'].lower():
                assert item['hymn_id'] is None, f"Hymn slot {item['slot_name']} in {setting} should not have a default hymn"
                assert item['file_path'] == "", f"Hymn slot {item['slot_name']} in {setting} should have an empty file path"


