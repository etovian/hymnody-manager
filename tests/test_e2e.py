import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db
from src.config import DEFAULT_MUSIC_DIR

client = TestClient(app)

def test_full_application_e2e_workflow(tmp_path):
    db_path = str(tmp_path / "e2e_app.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    os.environ["MUSIC_DIR"] = str(DEFAULT_MUSIC_DIR)
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
    os.environ["MUSIC_DIR"] = str(DEFAULT_MUSIC_DIR)
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
    os.environ["MUSIC_DIR"] = str(DEFAULT_MUSIC_DIR)
    init_db(db_path)

    scan_res = client.post("/api/scan")
    assert scan_res.status_code == 200

    res = client.get("/api/hymns")
    assert res.status_code == 200
    hymns = res.json()
    scanned_hymns = [h for h in hymns if h.get("disc_number") is not None and h.get("track_number") is not None]
    assert len(scanned_hymns) > 0

    for i in range(len(scanned_hymns) - 1):
        h1 = scanned_hymns[i]
        h2 = scanned_hymns[i + 1]
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


def test_audio_ended_event_auto_advances_or_updates_playlist():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    app_js_text = res.text

    # Extract the ended event listener block
    ended_index = app_js_text.find("audioPlayer.addEventListener('ended'")
    assert ended_index != -1, "ended event listener should be registered on audioPlayer"

    ended_block = app_js_text[ended_index:ended_index + 350]

    assert "renderMobilePlaylist(" in ended_block or "playNextTrack" in ended_block or "activeTrackIndex" in ended_block, "ended event listener should advance track or re-render mobile playlist"



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

    assert "function renderMobilePlaylist(service = mobileService)" in js, "renderMobilePlaylist signature should accept default service parameter"
    assert "function onMobileTrackClicked(" in js, "onMobileTrackClicked helper should be defined in app.js"
    assert "function toggleMobilePlayPause(" in js, "toggleMobilePlayPause helper should be defined in app.js"
    assert "function seekAudioMobile(" in js, "seekAudioMobile helper should be defined in app.js"
    assert "function onMobileServiceSelectChanged(" in js, "onMobileServiceSelectChanged function should be defined in app.js"
    assert "function renderMobileServiceInfo(" in js, "renderMobileServiceInfo function should be defined in app.js"
    assert "badge-playing" in js, "renderMobilePlaylist should render badge-playing class"
    assert "badge-paused" in js, "renderMobilePlaylist should render badge-paused class"
    assert "badge-missing-audio" in js, "renderMobilePlaylist should render badge-missing-audio class"
    assert "mobile-mode-active" in js, "switchView should toggle mobile-mode-active class on header"
    assert "mobile-inline-scrubber" in js, "renderMobilePlaylist active track card should include mobile-inline-scrubber"
    assert "mobile-inline-current" in js, "renderMobilePlaylist active track card should include mobile-inline-current"
    assert "mobile-inline-total" in js, "renderMobilePlaylist active track card should include mobile-inline-total"


def test_mobile_mode_task3_code_quality():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    # 1. updateMobileServiceDropdown auto-fetches full service details
    assert "onMobileServiceSelectChanged(selectedId)" in js

    # 2. Sync / Transport Service Resolution checks currentView === 'mobile'
    assert "currentView === 'mobile' && mobileService && mobileService.items" in js

    # 3. Catch audioPlayer.play() in playback helpers
    assert "audioPlayer.play().catch(" in js

    # 4. Error toast in onMobileServiceSelectChanged
    assert 'showToast("Failed to load service", "error", "Network Error")' in js

    # 5. Header element class toggle in switchView
    assert "headerEl.classList.toggle('mobile-mode-active', mode === 'mobile')" in js



def test_mobile_service_selection_api_e2e(tmp_path):
    db_path = str(tmp_path / "e2e_mobile_service.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    os.environ["MUSIC_DIR"] = str(DEFAULT_MUSIC_DIR)
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
    # Verify app.js contains function restartCurrentTrack and null safety checks for DOM elements
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    js = res_js.text
    assert "function restartCurrentTrack" in js
    assert "event.stopPropagation()" in js


def test_draggable_template_elements_html_and_top_save_button():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert 'id="drag-hymn-placeholder"' in html, "#drag-hymn-placeholder element must exist in index.html"
    assert 'id="drag-custom-slot"' in html, "#drag-custom-slot element must exist in index.html"
    assert 'draggable="true"' in html, "Draggable attribute must be enabled on template slot chips"
    assert 'addHymnPlaceholderSlotUI()' not in html, "Old + Hymn Placeholder button click handler should be replaced with draggable element"
    assert 'addCustomSlotUI()' not in html, "Old + Custom Slot button click handler should be replaced with draggable element"
    assert 'id="btn-save-template"' in html, "Save template button #btn-save-template must exist"

    # Verify Save Template button, template name, and description are in the top section before template-slots-editor-list
    save_idx = html.find('id="btn-save-template"')
    slots_idx = html.find('id="template-slots-editor-list"')
    name_idx = html.find('id="edit-template-name"')
    desc_idx = html.find('id="edit-template-desc"')
    drag_hymn_idx = html.find('id="drag-hymn-placeholder"')

    assert save_idx != -1 and slots_idx != -1 and name_idx != -1 and desc_idx != -1 and drag_hymn_idx != -1
    assert name_idx < slots_idx, "#edit-template-name must be in top panel before #template-slots-editor-list"
    assert desc_idx < slots_idx, "#edit-template-desc must be in top panel before #template-slots-editor-list"
    assert drag_hymn_idx < slots_idx, "#drag-hymn-placeholder must be in top panel before #template-slots-editor-list"
    assert save_idx < slots_idx, "#btn-save-template should be located in top header before #template-slots-editor-list"


def test_draggable_template_elements_js_logic():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    assert "function onNewTemplateSlotDragStart(" in js, "onNewTemplateSlotDragStart function should be defined in app.js"
    assert "draggedNewSlotType" in js, "draggedNewSlotType state variable should be defined in app.js"
    assert "new-template-slot" in js or "draggedNewSlotType" in js, "Drop handlers in app.js should handle new template slot types"


def test_draggable_template_elements_styles():
    res = client.get("/static/styles.css")
    assert res.status_code == 200
    css = res.text

    assert ".draggable-slot-chip" in css, "CSS rule for .draggable-slot-chip should exist in styles.css"
    assert "cursor: grab" in css or "cursor:grab" in css, "styles.css should specify grab cursor for draggable slot chips"


def test_hymnal_catalog_tune_and_source_ui_rendering_and_search_logic():
    res = client.get("/static/app.js")
    assert res.status_code == 200
    js = res.text

    assert "🎵 Tune:" in js, "app.js should render 🎵 Tune: metadata line in catalog item"
    assert "📜 Source:" in js, "app.js should render 📜 Source: metadata line in catalog item"
    assert "tune_name" in js, "app.js should reference tune_name for metadata rendering and search filtering"
    assert "source_meaning" in js, "app.js should reference source_meaning for metadata rendering and search filtering"


def test_hymn_details_modal_ui_and_js_logic():
    # 1. Verify index.html modal accessibility and structure
    res_html = client.get("/")
    assert res_html.status_code == 200
    html = res_html.text

    assert 'id="hymn-details-modal"' in html
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'aria-labelledby="modal-hymn-title"' in html
    assert 'aria-label="Close modal"' in html
    assert 'id="modal-history-container"' in html
    assert 'overflow-x: auto;' in html

    # 2. Verify app.js modal functions and interactions
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    js = res_js.text

    assert "function openHymnDetailsModal(" in js, "openHymnDetailsModal should be defined"
    assert "function closeHymnDetailsModal(" in js, "closeHymnDetailsModal should be defined"
    assert "btn-icon-info" in js, "btn-icon-info button should be rendered in catalog list"
    assert "openHymnDetailsModal(${h.id})" in js, "catalog list items and info buttons should invoke openHymnDetailsModal"
    assert "openHymnDetailsModal(${s.id})" in js, "sibling hymn cards should navigate to sibling hymn details"
    assert "/api/hymns/${hymnId}" in js, "modal should fetch enriched hymn details from API"
    assert "hymn-history-table" in js, "modal should render hymn-history-table for usage history"
    assert "sibling-hymn-card" in js, "modal should render sibling-hymn-card for tune siblings"
    assert "No previous service usage recorded for this hymn." in js
    assert "No other hymns in the catalog share this tune." in js
    assert "Escape" in js, "Escape key listener should close hymn details modal"


def test_hymn_details_modal_workflow_e2e(tmp_path):
    db_path = str(tmp_path / "e2e_modal_workflow.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)

    from src.database import get_db_connection, save_hymns

    # Identify seeded tunes from init_db
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tunes WHERE name = 'St. Thomas'")
        row = cursor.fetchone()
        tune_st_thomas = row["id"] if row else 1

        cursor.execute("SELECT id FROM tunes WHERE id != ? LIMIT 1", (tune_st_thomas,))
        row_other = cursor.fetchone()
        tune_other = row_other["id"] if row_other else 2

    # Clear catalog hymns to control exact test fixtures
    with get_db_connection(db_path) as conn:
        conn.cursor().execute("DELETE FROM hymns")
        conn.commit()

    audio_file_h1 = tmp_path / "hymn_331.m4a"
    audio_file_h1.write_bytes(b"AAC_AUDIO_DATA_FOR_HYMN_331" * 50)
    audio_file_h2 = tmp_path / "hymn_500.m4a"
    audio_file_h2.write_bytes(b"AAC_AUDIO_DATA_FOR_HYMN_500" * 50)
    audio_file_h3 = tmp_path / "hymn_700.m4a"
    audio_file_h3.write_bytes(b"AAC_AUDIO_DATA_FOR_HYMN_700" * 50)

    # 2. Seed test hymns sharing a tune, and test hymns with distinct tunes
    test_hymns = [
        {
            "id": 1001,
            "hymn_number": 331,
            "title": "The advent of our King",
            "disc_number": 1,
            "track_number": 1,
            "file_path": str(audio_file_h1),
            "liturgical_season": "Advent",
            "tune_id": tune_st_thomas,
            "source_code": "RC1900",
        },
        {
            "id": 1002,
            "hymn_number": 500,
            "title": "Creator Spirit, by Whose Aid",
            "disc_number": 1,
            "track_number": 2,
            "file_path": str(audio_file_h2),
            "liturgical_season": "Pentecost",
            "tune_id": tune_st_thomas,
            "source_code": "RC",
        },
        {
            "id": 1003,
            "hymn_number": 700,
            "title": "Love Divine, All Loves Excelling",
            "disc_number": 2,
            "track_number": 1,
            "file_path": str(audio_file_h3),
            "liturgical_season": "Praise",
            "tune_id": tune_other,
            "source_code": "Lu",
        },
    ]
    save_hymns(test_hymns, db_path=db_path)

    # 3. Seed test services and service items linking to the hymn
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Older service (2026-11-29)
        cursor.execute("""
            INSERT INTO services (id, service_date, title, liturgical_day, setting_preset, liturgical_color)
            VALUES (201, '2026-11-29', 'Advent Service 1', 'First Sunday in Advent', 'DS1', 'Blue')
        """)
        cursor.execute("""
            INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path, is_hymn_slot)
            VALUES (201, 1001, 'LSB 331 - The advent of our King', 'Hymn of Invocation', 1, ?, 1)
        """, (str(audio_file_h1),))

        # Newer service (2026-12-06)
        cursor.execute("""
            INSERT INTO services (id, service_date, title, liturgical_day, setting_preset, liturgical_color)
            VALUES (202, '2026-12-06', 'Advent Service 2', 'Second Sunday in Advent', 'DS2', 'Blue')
        """)
        cursor.execute("""
            INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path, is_hymn_slot)
            VALUES (202, 1001, 'LSB 331 - The advent of our King', 'Hymn of the Day', 5, ?, 1)
        """, (str(audio_file_h1),))
        conn.commit()

    # 4. Use FastAPI TestClient to fetch GET /api/hymns/{id}
    res = client.get("/api/hymns/1001")
    assert res.status_code == 200
    hymn = res.json()

    # Verify base metadata includes tune_name and source_meaning
    assert hymn["id"] == 1001
    assert hymn["hymn_number"] == 331
    assert hymn["title"] == "The advent of our King"
    assert hymn["tune_name"] == "St. Thomas"
    assert hymn["source_meaning"] == "Roman Catholic hymns to 1900"

    # Verify usage_history contains correct historical entries ordered by date descending
    history = hymn.get("usage_history", [])
    assert len(history) == 2

    assert history[0]["service_date"] == "2026-12-06"
    assert history[0]["liturgical_day"] == "Second Sunday in Advent"
    assert history[0]["setting_preset"] == "DS2"
    assert history[0]["service_title"] == "Advent Service 2"
    assert history[0]["slot_name"] == "Hymn of the Day"

    assert history[1]["service_date"] == "2026-11-29"
    assert history[1]["liturgical_day"] == "First Sunday in Advent"
    assert history[1]["setting_preset"] == "DS1"
    assert history[1]["service_title"] == "Advent Service 1"
    assert history[1]["slot_name"] == "Hymn of Invocation"

    # Verify same_tune_hymns contains sibling hymns sharing tune_id and excludes parent hymn itself
    siblings = hymn.get("same_tune_hymns", [])
    assert len(siblings) == 1
    assert siblings[0]["id"] == 1002
    assert siblings[0]["hymn_number"] == 500
    assert siblings[0]["title"] == "Creator Spirit, by Whose Aid"
    assert siblings[0]["tune_name"] == "St. Thomas"
    assert all(s["id"] != 1001 for s in siblings)
    assert all(s["id"] != 1003 for s in siblings)

    # Sibling hymn audio endpoint can be reached via range streaming
    stream_res = client.get(f"/api/hymns/{siblings[0]['id']}/audio", headers={"Range": "bytes=0-100"})
    assert stream_res.status_code in (200, 206)
    if stream_res.status_code == 206:
        assert "bytes 0-100/" in stream_res.headers.get("content-range", "")
        assert len(stream_res.content) == 101

    # 5. Verify index.html contains all modal element IDs, ARIA attributes, and .btn-icon-info buttons
    index_res = client.get("/")
    assert index_res.status_code == 200
    html = index_res.text

    modal_element_ids = [
        "hymn-details-modal",
        "modal-hymn-title",
        "modal-hymn-subtitle",
        "modal-metadata-bar",
        "modal-history-heading",
        "modal-history-container",
        "modal-tune-heading",
        "modal-siblings-container",
    ]
    for el_id in modal_element_ids:
        assert f'id="{el_id}"' in html, f"Missing modal element ID: {el_id}"

    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'aria-labelledby="modal-hymn-title"' in html
    assert 'aria-label="Close modal"' in html

    # Verify .btn-icon-info button rendering and styling
    app_res = client.get("/static/app.js")
    assert app_res.status_code == 200
    assert "btn-icon-info" in app_res.text

    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    assert ".btn-icon-info" in css_res.text


def test_catalog_unprinted_hymnal_badge_rendering():
    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".badge-not-in-hymnal" in css

    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "badge-not-in-hymnal" in js
    assert "in_printed_hymnal === false" in js or "in_printed_hymnal" in js

    # Verify title is on top row and badges on the second row
    title_idx = js.find("${escapeHtml(h.title)}")
    badge_idx = js.find("${numTag}</span>${unprintedBadge}")
    assert title_idx != -1 and badge_idx != -1
    assert title_idx < badge_idx, "Hymn title should appear in the row above the badges"


def test_hymn_details_modal_unprinted_banner():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert "modal-warning-banner" in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".modal-warning-banner" in css

    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()
    assert "modal-warning-banner" in js
    assert "in_printed_hymnal === false" in js


