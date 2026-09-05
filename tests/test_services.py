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
    ds3_salutation = next((i for i in items if i['match_term'] == "DS3 - Salutation"), None)
    assert ds3_salutation is not None, "DS3 template must have an item with match_term 'DS3 - Salutation'"
    
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

def test_matins_and_vespers_canticles_matching(tmp_path):
    db_path = str(tmp_path / "matins_vespers_test.db")
    init_db(db_path)
    
    # Save dummy canticles for Matins and Vespers matching actual CPH track titles
    save_hymns([
        {
            'hymn_number': None,
            'title': 'MA - Antiphon & Venite',
            'disc_number': 31,
            'track_number': 4,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\31-04 MA - Antiphon & Venite.m4a',
            'liturgical_season': 'General'
        },
        {
            'hymn_number': None,
            'title': 'MA - Te Deum',
            'disc_number': 31,
            'track_number': 10,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\31-10 MA - Te Deum.m4a',
            'liturgical_season': 'General'
        },
        {
            'hymn_number': None,
            'title': 'VE - Magnificat',
            'disc_number': 31,
            'track_number': 27,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'c:\dev\IdeaProjects\hymnody-manager\music\31-27 VE - Magnificat.m4a',
            'liturgical_season': 'General'
        }
    ], db_path)
    
    matins_id = create_service_from_preset("Matins Service", "2026-09-01", setting_preset="Matins", db_path=db_path)
    matins = get_service_details(matins_id, db_path=db_path)
    
    venite = next((i for i in matins['items'] if i['slot_name'] == "Venite"), None)
    te_deum = next((i for i in matins['items'] if i['slot_name'] == "Te Deum"), None)
    
    assert venite is not None and venite['hymn_id'] is not None, "Venite should bind to MA - Antiphon & Venite track"
    assert te_deum is not None and te_deum['hymn_id'] is not None, "Te Deum should bind to MA - Te Deum track"

    vespers_id = create_service_from_preset("Vespers Service", "2026-09-01", setting_preset="Vespers", db_path=db_path)
    vespers = get_service_details(vespers_id, db_path=db_path)
    magnificat = next((i for i in vespers['items'] if i['slot_name'] == "Magnificat"), None)
    assert magnificat is not None and magnificat['hymn_id'] is not None, "Magnificat should bind to VE - Magnificat track"

def test_all_preset_canticles_bind_successfully(tmp_path):
    from src.services import PRESETS, create_service_from_preset, get_service_details
    from src.database import save_hymns
    db_path = str(tmp_path / "all_presets_test.db")
    init_db(db_path)
    
    # Save CPH canticle track titles for DS1-DS5, Matins, Vespers
    save_hymns([
        {'hymn_number': None, 'title': 'DS1 - Kyrie_ Intonation', 'disc_number': 30, 'track_number': 1, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-01.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Gloria in Excelsis', 'disc_number': 30, 'track_number': 7, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-07.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Salutation', 'disc_number': 30, 'track_number': 9, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-09.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Collect of the Day_ Amen', 'disc_number': 30, 'track_number': 10, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-10.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Offertory', 'disc_number': 30, 'track_number': 15, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-15.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Sanctus', 'disc_number': 30, 'track_number': 20, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-20.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Agnus Dei', 'disc_number': 30, 'track_number': 23, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-23.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS1 - Nunc Dimittis', 'disc_number': 30, 'track_number': 25, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-25.m4a', 'liturgical_season': 'Liturgical'},

        {'hymn_number': None, 'title': 'DS2 - Kyrie_ Intonation', 'disc_number': 30, 'track_number': 30, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-30.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Gloria in Excelsis', 'disc_number': 30, 'track_number': 36, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-36.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Salutation', 'disc_number': 30, 'track_number': 38, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-38.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Collect of the Day_ Amen', 'disc_number': 30, 'track_number': 39, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-39.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Offertory', 'disc_number': 30, 'track_number': 44, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-44.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Sanctus', 'disc_number': 30, 'track_number': 49, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-49.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Agnus Dei', 'disc_number': 30, 'track_number': 52, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-52.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS2 - Nunc Dimittis', 'disc_number': 30, 'track_number': 54, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-54.m4a', 'liturgical_season': 'Liturgical'},

        {'hymn_number': None, 'title': 'DS3 - Kyrie', 'disc_number': 30, 'track_number': 60, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-60.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Gloria in Excelsis', 'disc_number': 30, 'track_number': 61, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-61.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Salutation', 'disc_number': 30, 'track_number': 62, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-62.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Collect of the Day_ Amen', 'disc_number': 30, 'track_number': 63, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-63.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Offertory', 'disc_number': 30, 'track_number': 68, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-68.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Sanctus', 'disc_number': 30, 'track_number': 73, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-73.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Pax Domini_ Amen & Agnus Dei', 'disc_number': 30, 'track_number': 76, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-76.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS3 - Nunc Dimittis', 'disc_number': 30, 'track_number': 77, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-77.m4a', 'liturgical_season': 'Liturgical'},

        {'hymn_number': None, 'title': 'DS4 - Kyrie_ One Time', 'disc_number': 30, 'track_number': 83, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-83.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS4 - Gloria in Excelsis', 'disc_number': 30, 'track_number': 86, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-86.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS4 - Sanctus', 'disc_number': 30, 'track_number': 88, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-88.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS4 - Agnus Dei', 'disc_number': 30, 'track_number': 89, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-89.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS4 - Nunc Dimittis', 'disc_number': 30, 'track_number': 90, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-90.m4a', 'liturgical_season': 'Liturgical'},

        {'hymn_number': None, 'title': 'DS5 - Kyrie (LSB 942)', 'disc_number': 30, 'track_number': 91, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-91.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS5 - Gloria in Excelsis (LSB 948)', 'disc_number': 30, 'track_number': 92, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-92.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS5 - Sanctus (LSB 960)', 'disc_number': 30, 'track_number': 94, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-94.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS5 - Agnus Dei (LSB 198)', 'disc_number': 30, 'track_number': 95, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-95.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'DS5 - Post-Communion Hymn (LSB 617)', 'disc_number': 30, 'track_number': 96, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\30-96.m4a', 'liturgical_season': 'Liturgical'},

        {'hymn_number': None, 'title': 'MA - Versicles_ Intonation', 'disc_number': 31, 'track_number': 1, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-01.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Antiphon & Venite', 'disc_number': 31, 'track_number': 4, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-04.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Responsory_ Intonation', 'disc_number': 31, 'track_number': 6, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-06.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Te Deum', 'disc_number': 31, 'track_number': 10, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-10.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Benedictus', 'disc_number': 31, 'track_number': 11, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-11.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Collect_ Amen', 'disc_number': 31, 'track_number': 16, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-16.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Benedicamus', 'disc_number': 31, 'track_number': 17, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-17.m4a', 'liturgical_season': 'Liturgical'},
        {'hymn_number': None, 'title': 'MA - Benediction_ Amen', 'disc_number': 31, 'track_number': 18, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-18.m4a', 'liturgical_season': 'Liturgical'},

        {'hymn_number': None, 'title': 'VE - Magnificat', 'disc_number': 31, 'track_number': 27, 'album': 'CPH', 'artist': 'CPH', 'year': 2009, 'file_path': r'c:\music\31-27.m4a', 'liturgical_season': 'Liturgical'}
    ], db_path)

    for preset_name in PRESETS:
        s_id = create_service_from_preset(f"Test {preset_name}", "2026-09-01", setting_preset=preset_name, db_path=db_path)
        details = get_service_details(s_id, db_path=db_path)
        for item in details['items']:
            if item['slot_name'] not in ['Opening Hymn', 'Hymn of the Day', 'Distribution 1', 'Distribution 2', 'Closing Hymn', 'Office Hymn']:
                assert item['hymn_id'] is not None, f"Canticle slot {item['slot_name']} in preset {preset_name} failed to bind audio track"
                assert item['file_path'] != "", f"Canticle slot {item['slot_name']} in preset {preset_name} has empty file_path"

def test_matins_full_template_items(tmp_path):
    from src.services import get_template_by_name, seed_templates_if_empty
    db_path = str(tmp_path / "matins_template_test.db")
    init_db(db_path)
    seed_templates_if_empty(db_path)
    
    matins = get_template_by_name("Matins", db_path)
    assert matins is not None
    slot_names = [i['slot_name'] for i in matins['items']]
    
    expected = [
        "Opening Hymn", "Versicles", "Venite", "Office Hymn",
        "Responsory", "Te Deum", "Benedictus",
        "Collect for Grace", "Benedicamus", "Benediction", "Closing Hymn"
    ]
    for req in expected:
        assert req in slot_names, f"Matins template missing required item: {req}"


def test_create_service_matins_common_no_duplicate_antiphon_track(tmp_path):
    from src.services import save_template, create_service_from_preset, get_service_details
    db_path = str(tmp_path / "matins_common_dup_test.db")
    init_db(db_path)

    # Save audio tracks for MA - Antiphon & Venite (Track 4) and MA - Antiphon (Track 5)
    save_hymns([
        {
            'hymn_number': None,
            'title': 'MA - Antiphon & Venite',
            'disc_number': 31,
            'track_number': 4,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'C:\music\31-04 MA - Antiphon & Venite.m4a',
            'liturgical_season': 'General'
        },
        {
            'hymn_number': None,
            'title': 'MA - Antiphon',
            'disc_number': 31,
            'track_number': 5,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': r'C:\music\31-05 MA - Antiphon.m4a',
            'liturgical_season': 'General'
        }
    ], db_path)

    # Create template "Matins (Common)" with two slots
    t_id = save_template(
        name="Matins (Common)",
        description="Custom Matins Template",
        items=[
            {'slot_name': 'MA - Antiphon & Venite', 'match_term': 'MA - Antiphon & Venite', 'item_title': 'MA - Antiphon & Venite'},
            {'slot_name': 'MA - Antiphon', 'match_term': 'MA - Antiphon', 'item_title': 'MA - Antiphon'}
        ],
        db_path=db_path
    )

    s_id = create_service_from_preset("Test Matins Common", "2026-09-05", setting_preset="Matins (Common)", db_path=db_path)
    srv = get_service_details(s_id, db_path=db_path)
    items = srv['items']

    assert len(items) == 2
    assert items[0]['item_title'] == 'MA - Antiphon & Venite'
    assert items[0]['file_path'] == r'C:\music\31-04 MA - Antiphon & Venite.m4a'

    assert items[1]['item_title'] == 'MA - Antiphon', f"Expected slot 2 to bind 'MA - Antiphon', but got '{items[1]['item_title']}'"
    assert items[1]['file_path'] == r'C:\music\31-05 MA - Antiphon.m4a'






