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


def test_right_panel_tabs_and_template_selector_html():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert 'id="tab-service-planner"' in html, "Tab 1 button #tab-service-planner should exist in index.html"
    assert 'id="tab-template-editor"' in html, "Tab 2 button #tab-template-editor should exist in index.html"
    assert 'id="panel-service-planner"' in html, "Service planner panel #panel-service-planner should exist"
    assert 'id="panel-template-editor"' in html, "Template editor panel #panel-template-editor should exist"
    assert 'id="template-selector-modal"' in html, "Template selector modal #template-selector-modal should exist"
    assert 'id="btn-open-template-modal"' in html, "Button to open template selector modal should exist"


def test_tabbed_template_editor_js_functions():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    assert "function switchPlannerTab(" in js, "switchPlannerTab function should be defined in app.js"
    assert "function openTemplateSelectorModal(" in js, "openTemplateSelectorModal function should be defined in app.js"
    assert "function closeTemplateSelectorModal(" in js, "closeTemplateSelectorModal function should be defined in app.js"
    assert "function renderTemplateCardsModal(" in js, "renderTemplateCardsModal function should be defined in app.js"
    assert "function selectTemplateFromModal(" in js, "selectTemplateFromModal function should be defined in app.js"
    assert "function duplicateTemplateFromModal(" in js, "duplicateTemplateFromModal function should be defined in app.js"
    assert "function createNewTemplateFromModal(" in js, "createNewTemplateFromModal function should be defined in app.js"


def test_create_and_save_custom_template_in_tab2(tmp_path):
    db_path = str(tmp_path / "e2e_template_save.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)

    # 1. Create a custom template via API
    create_res = client.post("/api/templates", json={
        "name": "Custom Matins Variation",
        "description": "Custom liturgy preset",
        "items": [
            {"slot_name": "Opening Hymn", "match_term": "HYMN_SLOT", "item_title": "Opening Hymn"},
            {"slot_name": "Versicles", "match_term": "MA - Versicles_ Intonation", "item_title": "Versicles"}
        ]
    })
    assert create_res.status_code == 200
    tmpl = create_res.json()
    assert tmpl["name"] == "Custom Matins Variation"
    t_id = tmpl["id"]

    # 2. Get list of templates
    list_res = client.get("/api/templates")
    assert list_res.status_code == 200
    tmpls = list_res.json()
    assert any(t["name"] == "Custom Matins Variation" for t in tmpls)

    # 3. Create service using the custom setting preset
    srv_res = client.post("/api/services", json={
        "title": "Custom Matins Service",
        "service_date": "2026-09-06",
        "setting_preset": "Custom Matins Variation"
    })
    assert srv_res.status_code == 200
    srv = srv_res.json()
    assert srv["setting_preset"] == "Custom Matins Variation"
    assert len(srv["items"]) == 2

    # 4. Delete custom template
    del_res = client.delete(f"/api/templates/{t_id}")
    assert del_res.status_code == 200


def test_template_drag_and_drop_insertion_logic():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    assert "onTemplateSlotDragOver" in js, "onTemplateSlotDragOver function should be defined in app.js"
    assert "onTemplateSlotDragLeave" in js, "onTemplateSlotDragLeave function should be defined in app.js"
    assert "insert-above" in js and "insert-below" in js


def test_play_template_slot_track_function():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    assert "function playTemplateSlotTrack(" in js, "playTemplateSlotTrack helper function should be defined in app.js"
    assert "playTemplateSlotTrack(" in js, "playTemplateSlotTrack should be called from template slot cards"
    assert 'showToast(`Slot "${item.slot_name}" is a generic hymn placeholder' in js or 'showToast(' in js
    assert "alert(" not in js, "All alert() browser popups in app.js must be replaced with showToast()"


def test_template_drag_and_drop_styles_and_event_stop_propagation():
    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    css = css_res.text
    assert ".template-slot-card.drag-insert-above" in css, "CSS rule for .template-slot-card.drag-insert-above should exist"
    assert ".template-slot-card.drag-insert-below" in css, "CSS rule for .template-slot-card.drag-insert-below should exist"
    assert ".template-slot-card.drag-replace" in css, "CSS rule for .template-slot-card.drag-replace should exist"

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    js = js_res.text
    assert "e.stopPropagation()" in js, "e.stopPropagation() should be used in slot drop handlers to prevent event bubbling"


def test_client_side_draft_service_exact_title_match_in_app_js():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text
    assert "exactMatch = allTracks.find" in js, "createDraftServiceLocally in app.js must prioritize exact title matches"
    assert "prefixMatch = exactMatch || allTracks.find" in js, "createDraftServiceLocally in app.js must prioritize prefix matches before substring matches"


def test_index_contains_toast_container():
    res = client.get("/")
    assert res.status_code == 200
    assert '<div id="toast-container"' in res.text


def test_app_js_includes_show_toast():
    res = client.get("/static/app.js?v=2")
    assert res.status_code == 200
    assert "function showToast" in res.text
    assert "let selectedTemplateForEdit =" in res.text, "selectedTemplateForEdit must be declared at module scope in app.js"


def test_mobile_mode_task3_js_functions():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    assert "function toggleMobileTrack(" in js, "toggleMobileTrack function should be defined in app.js"
    assert "function renderMobilePlaylist(" in js, "renderMobilePlaylist function should be defined in app.js"
    assert "function onMobileServiceSelectChanged(" in js, "onMobileServiceSelectChanged function should be defined in app.js"
    assert "function renderMobileServiceInfo(" in js, "renderMobileServiceInfo function should be defined in app.js"
    assert "badge-playing" in js, "renderMobilePlaylist should render badge-playing class"
    assert "badge-paused" in js, "renderMobilePlaylist should render badge-paused class"
    assert "badge-missing-audio" in js, "renderMobilePlaylist should render badge-missing-audio class"


def test_mobile_mode_task3_code_quality():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    # 1. updateMobileServiceDropdown auto-fetches full service details
    assert "onMobileServiceSelectChanged(selectedId)" in js

    # 2. Sync / Transport Service Resolution checks currentView === 'mobile'
    assert "currentView === 'mobile' && mobileService && mobileService.items" in js

    # 3. Catch audioPlayer.play() in toggleMobileTrack
    assert "audioPlayer.play().catch(" in js

    # 4. Error toast in onMobileServiceSelectChanged
    assert 'showToast("Failed to load service", "error", "Network Error")' in js


def test_mobile_service_selection_api_e2e(tmp_path):
    db_path = str(tmp_path / "e2e_mobile_service.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    os.environ["MUSIC_DIR"] = r"c:\dev\IdeaProjects\hymnody-manager\music"
    init_db(db_path)

    # 1. Populate database with audio tracks
    scan_res = client.post("/api/scan")
    assert scan_res.status_code == 200

    # 2. Create service plans for mobile selection
    srv1_res = client.post("/api/services", json={
        "title": "Divine Service 1 Sanctuary",
        "service_date": "2026-09-13",
        "setting_preset": "DS1",
        "liturgical_color": "Green",
        "liturgical_day": "16th Sunday after Trinity"
    })
    assert srv1_res.status_code == 200
    srv1 = srv1_res.json()
    srv1_id = srv1["id"]

    srv2_res = client.post("/api/services", json={
        "title": "Evening Vespers Service",
        "service_date": "2026-09-20",
        "setting_preset": "Vespers",
        "liturgical_color": "Violet"
    })
    assert srv2_res.status_code == 200
    srv2_id = srv2_res.json()["id"]

    # 3. Retrieve service list for mobile selector (/api/services)
    services_res = client.get("/api/services")
    assert services_res.status_code == 200
    services_list = services_res.json()
    assert len(services_list) == 2
    service_ids = [s["id"] for s in services_list]
    assert srv1_id in service_ids
    assert srv2_id in service_ids

    # 4. Fetch specific service details including `items` payload for mobile mode playback (/api/services/{id})
    detail_res = client.get(f"/api/services/{srv1_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert detail["id"] == srv1_id
    assert detail["title"] == "Divine Service 1 Sanctuary"
    assert detail["setting_preset"] == "DS1"
    assert "items" in detail
    assert isinstance(detail["items"], list)
    assert len(detail["items"]) > 0

    # Verify items contain necessary metadata for mobile playback execution
    for item in detail["items"]:
        assert "sequence_order" in item
        assert "slot_name" in item
        assert "item_title" in item
        assert "file_path" in item

    # 5. Non-existent service ID returns 404
    invalid_res = client.get("/api/services/999999")
    assert invalid_res.status_code == 404


def test_mobile_track_restart_logic():
    # Verify index.html contains mobile restart button with restartCurrentTrack() click handler and disabled attribute
    res_index = client.get("/")
    assert res_index.status_code == 200
    html = res_index.text
    assert '<button type="button" id="mobile-restart-btn"' in html
    assert 'onclick="restartCurrentTrack()"' in html
    assert 'disabled' in html

    # Verify app.js contains function restartCurrentTrack()
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    js = res_js.text
    assert "function restartCurrentTrack()" in js

    # Verify styles.css contains .mobile-restart-btn rules
    res_css = client.get("/static/styles.css")
    assert res_css.status_code == 200
    css = res_css.text
    assert ".mobile-restart-btn" in css

