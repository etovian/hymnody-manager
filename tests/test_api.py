import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db, save_hymns
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
