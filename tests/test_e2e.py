import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db

client = TestClient(app)

def test_full_application_e2e_workflow(tmp_path):
    db_path = str(tmp_path / "e2e_app.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    os.environ["MUSIC_DIR"] = r"c:\dev\IdeaProjects\hymnody-manager\music"
    init_db(db_path)
    
    # 1. Rescan music directory
    scan_res = client.post("/api/scan")
    assert scan_res.status_code == 200
    assert scan_res.json()["count"] > 300
    
    # 2. Query Advent hymns
    search_res = client.get("/api/hymns?q=331")
    assert search_res.status_code == 200
    hymns = search_res.json()
    assert len(hymns) > 0
    assert hymns[0]['hymn_number'] == 331
    h_id = hymns[0]['id']
    
    # 3. Stream audio range request
    stream_res = client.get(f"/api/hymns/{h_id}/audio", headers={"Range": "bytes=0-1024"})
    assert stream_res.status_code in (200, 206)
    
    # 4. Create Divine Service 2 (DS2) service plan
    srv_res = client.post("/api/services", json={
        "title": "1st Sunday in Advent",
        "service_date": "2026-11-29",
        "setting_preset": "DS2",
        "liturgical_color": "Blue"
    })
    assert srv_res.status_code == 200
    srv = srv_res.json()
    assert srv["title"] == "1st Sunday in Advent"
    srv_id = srv["id"]
    
    # 5. Verify canticle tracks auto-populated
    items = srv["items"]
    assert len(items) >= 8
    assert any("Kyrie" in item["item_title"] or "Kyrie" in item["slot_name"] for item in items)
    
    # 6. Assign LSB 331 to Opening Hymn slot
    items[0]["hymn_id"] = h_id
    items[0]["item_title"] = "LSB 331 - The advent of our King"
    items[0]["file_path"] = hymns[0]["file_path"]
    
    update_res = client.put(f"/api/services/{srv_id}/items", json=items)
    assert update_res.status_code == 200
    updated_srv = update_res.json()
    assert updated_srv["items"][0]["hymn_id"] == h_id
    
    # 7. Export Mobile Package Zip
    zip_res = client.get(f"/api/services/{srv_id}/export/zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert len(zip_res.content) > 1000
    
    # 8. Web Index Page serving
    index_res = client.get("/")
    assert index_res.status_code == 200
    assert "Hymnody Manager" in index_res.text


def test_dual_tab_hymnal_catalog_e2e(tmp_path):
    db_path = str(tmp_path / "e2e_dual_tab.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    os.environ["MUSIC_DIR"] = r"c:\dev\IdeaProjects\hymnody-manager\music"
    init_db(db_path)

    # Rescan directory to populate DB
    scan_res = client.post("/api/scan")
    assert scan_res.status_code == 200

    # Query category_type=hymn
    hymns_res = client.get("/api/hymns?category_type=hymn")
    assert hymns_res.status_code == 200
    hymns = hymns_res.json()
    assert len(hymns) > 0
    assert all(h["hymn_number"] is not None for h in hymns)

    # Query category_type=liturgy
    liturgy_res = client.get("/api/hymns?category_type=liturgy")
    assert liturgy_res.status_code == 200
    liturgy_items = liturgy_res.json()
    assert len(liturgy_items) > 0
    assert all(item["hymn_number"] is None for item in liturgy_items)


def test_alphabetized_filters_and_sorting(tmp_path):
    db_path = str(tmp_path / "e2e_sorting.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    os.environ["MUSIC_DIR"] = r"c:\dev\IdeaProjects\hymnody-manager\music"
    init_db(db_path)

    scan_res = client.post("/api/scan")
    assert scan_res.status_code == 200

    res = client.get("/api/hymns")
    assert res.status_code == 200
    hymns = res.json()
    assert len(hymns) > 0

    for i in range(len(hymns) - 1):
        h1 = hymns[i]
        h2 = hymns[i + 1]
        assert (h1["disc_number"], h1["track_number"]) <= (h2["disc_number"], h2["track_number"])


def test_catalog_play_button_rendering():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    app_js_text = res.text

    # Assert helper function exists
    assert "function playCatalogHymn(" in app_js_text, "playCatalogHymn helper function should be defined in app.js"

    # Assert ▶ Play button is rendered in hymnal catalog and template editor search
    assert "playCatalogHymn(" in app_js_text
    assert "▶ Play" in app_js_text
    assert 'onclick="handleCatalogAddClick' not in app_js_text, "+ Add button should be replaced with Play button in catalog list and template editor"


def test_audio_ended_event_stops_playback_without_auto_advance():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    app_js_text = res.text

    # Extract the ended event listener block
    ended_index = app_js_text.find("audioPlayer.addEventListener('ended'")
    assert ended_index != -1, "ended event listener should be registered on audioPlayer"

    ended_block = app_js_text[ended_index:ended_index + 200]

    assert "playNextTrack()" not in ended_block, "ended event listener should not auto advance using playNextTrack()"
    assert "isPlaying = false" in ended_block, "ended event listener should set isPlaying to false"
    assert "updatePlayButtonUI()" in ended_block, "ended event listener should update play button UI"




