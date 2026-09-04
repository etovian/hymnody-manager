import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db, save_hymns, normalize_path

from src.services import create_service_from_preset

client = TestClient(app)

def test_full_api_workflow(tmp_path):
    db_path = str(tmp_path / "api_full_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
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
    
    # 1. Search hymns API
    res = client.get("/api/hymns?q=331")
    assert res.status_code == 200
    hymns = res.json()
    assert len(hymns) == 1
    h_id = hymns[0]['id']
    
    # 2. Audio Streaming Range Request
    stream_res = client.get(f"/api/hymns/{h_id}/audio", headers={"Range": "bytes=0-100"})
    assert stream_res.status_code in (200, 206)
    
    # 3. Create Service API
    srv_res = client.post("/api/services", json={
        "title": "Advent Service",
        "service_date": "2026-11-29",
        "setting_preset": "DS2"
    })
    assert srv_res.status_code == 200
    srv_id = srv_res.json()["id"]
    
    # 4. Get Service API
    get_srv = client.get(f"/api/services/{srv_id}")
    assert get_srv.status_code == 200
    assert get_srv.json()["title"] == "Advent Service"
    
    # 5. Export Service Zip API
    zip_res = client.get(f"/api/services/{srv_id}/export/zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert zip_res.headers["content-disposition"] == 'attachment; filename="20261129_DS2.zip"'

def test_template_and_metadata_api_endpoints(tmp_path):
    db_path = str(tmp_path / "api_templates_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    # 1. Get templates list
    res = client.get("/api/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 7
    
    # 2. Update service metadata
    srv_res = client.post("/api/services", json={
        "title": "Initial Service",
        "service_date": "2026-09-01",
        "setting_preset": "DS3"
    })
    srv_id = srv_res.json()["id"]
    
    meta_res = client.put(f"/api/services/{srv_id}/metadata", json={
        "service_date": "2026-09-06",
        "liturgical_day": "15th Sunday after Trinity",
        "title": "Trinity Service"
    })
    assert meta_res.status_code == 200
    srv_data = meta_res.json()
    assert srv_data["service_date"] == "2026-09-06"
    assert srv_data["liturgical_day"] == "15th Sunday after Trinity"
    assert srv_data["title"] == "Trinity Service"
    
    # 3. Duplicate Service
    dup_res = client.post(f"/api/services/{srv_id}/duplicate", json={"new_date": "2026-09-13"})
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    assert dup_data["service_date"] == "2026-09-13"
    assert "Copy" in dup_data["title"]
    
    # 4. Analytics
    ana_res = client.get("/api/analytics/hymns")
    assert ana_res.status_code == 200
    assert isinstance(ana_res.json(), list)

def test_custom_template_with_specific_audio_track_and_reordering(tmp_path):
    db_path = str(tmp_path / "custom_template_audio_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    res = client.post("/api/templates", json={
        "name": "Custom DS3 Variant",
        "description": "DS3 with Salutation audio track",
        "items": [
            {"slot_name": "Opening Hymn", "match_term": "HYMN_SLOT", "item_title": "Opening Hymn"},
            {"slot_name": "DS3 - Salutation", "match_term": "DS3 - Salutation", "item_title": "DS3 - Salutation"},
            {"slot_name": "DS3 - Collect of the Day", "match_term": "DS3 - Collect of the Day", "item_title": "DS3 - Collect of the Day"},
            {"slot_name": "Closing Hymn", "match_term": "HYMN_SLOT", "item_title": "Closing Hymn"}
        ]
    })
    assert res.status_code == 200
    tmpl = res.json()
    assert tmpl["name"] == "Custom DS3 Variant"
    assert len(tmpl["items"]) == 4
    assert tmpl["items"][1]["match_term"] == "DS3 - Salutation"

def test_create_service_from_template_with_bound_audio_track(tmp_path):
    from src.database import save_hymns
    from src.services import create_service_from_preset, get_service_details
    
    db_path = str(tmp_path / "bound_audio_service_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    # Add DS3 - Salutation audio track to DB
    save_hymns([{
        "title": "DS3 - Salutation",
        "hymn_number": "",
        "disc_number": 30,
        "track_number": 62,
        "album": "Divine Service 3",
        "artist": "Concordia Organist",
        "year": 2006,
        "liturgical_season": "Liturgical",
        "file_path": "c:/music/ds3_salutation.m4a"
    }], db_path=db_path)
    
    # Create template
    t_res = client.post("/api/templates", json={
        "name": "Template With Salutation",
        "description": "Custom template",
        "items": [
            {"slot_name": "Salutation", "match_term": "DS3 - Salutation", "item_title": "Salutation"}
        ]
    })
    tmpl_id = t_res.json()["id"]
    
    # Generate service using preset/template name
    srv = create_service_from_preset("Sunday Worship", "2026-09-01", "Template With Salutation", db_path=db_path)
    details = get_service_details(srv, db_path=db_path)
    
    assert len(details["items"]) == 1
    assert details["items"][0]["item_title"] == "DS3 - Salutation"
    assert details["items"][0]["file_path"] == normalize_path("c:/music/ds3_salutation.m4a")

def test_export_invalid_service_id_returns_404(tmp_path):
    db_path = str(tmp_path / "export_404_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    res = client.get("/api/services/99999/export/zip")
    assert res.status_code == 404

def test_export_service_zip_filename_header(tmp_path):
    db_path = str(tmp_path / "export_filename_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    srv_res = client.post("/api/services", json={
        "title": "Pentecost Service",
        "service_date": "2026-09-01",
        "setting_preset": "DS3",
        "liturgical_day": "Pentecost 15"
    })
    assert srv_res.status_code == 200
    srv_id = srv_res.json()["id"]
    
    res = client.get(f"/api/services/{srv_id}/export/zip")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert res.headers["content-disposition"] == 'attachment; filename="20260901_DS3_Pentecost_15.zip"'

def test_api_get_hymns_category_type_filter(tmp_path):
    db_path = str(tmp_path / "api_category_type_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    save_hymns([
        {
            'hymn_number': 331,
            'title': 'The advent of our King',
            'disc_number': 1,
            'track_number': 1,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': 'c:/music/hymn_331.m4a',
            'liturgical_season': 'Advent'
        },
        {
            'hymn_number': None,
            'title': 'DS2 - Kyrie',
            'disc_number': 30,
            'track_number': 1,
            'album': 'Divine Service 2',
            'artist': 'Concordia Publishing House',
            'year': 2006,
            'file_path': 'c:/music/ds2_kyrie.m4a',
            'liturgical_season': 'Liturgical'
        }
    ], db_path)
    
    res_hymn = client.get("/api/hymns?category_type=hymn")
    assert res_hymn.status_code == 200
    hymns = res_hymn.json()
    assert len(hymns) == 1
    assert hymns[0]['title'] == 'The advent of our King'
    
    res_liturgy = client.get("/api/hymns?category_type=liturgy")
    assert res_liturgy.status_code == 200
    liturgies = res_liturgy.json()
    assert len(liturgies) == 1
    assert liturgies[0]['title'] == 'DS2 - Kyrie'





