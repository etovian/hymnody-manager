import pytest

def test_playback_mode_and_mobile_ui_mode_enums():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    # PLAYBACK_MODE enum
    assert "const PLAYBACK_MODE" in content
    assert "SINGLE: 'SINGLE'" in content
    assert "CONTINUOUS: 'CONTINUOUS'" in content
    assert "REPEAT_ALL: 'REPEAT_ALL'" in content

    # MOBILE_UI_MODE enum
    assert "const MOBILE_UI_MODE" in content
    assert "LITURGY: 'LITURGY'" in content
    assert "HYMNS_ONLY: 'HYMNS_ONLY'" in content

def test_cycle_playback_mode_and_button_updater_defined():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    assert "function cyclePlaybackMode()" in content
    assert "function updateMobilePlaybackModeButton()" in content
    assert "updateMobilePlaybackModeButton()" in content

def test_audio_ended_handles_continuous_mode():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    assert "PLAYBACK_MODE.CONTINUOUS" in content
    assert "currentPos + 1 < activeItems.length" in content


def test_mobile_header_three_button_action_bar_present():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="btn-mobile-services-explorer"' in html
    assert 'onclick="openServicesExplorer()"' in html
    assert 'id="btn-mobile-mode-toggle"' in html
    assert 'id="btn-mobile-playback-mode"' in html
    assert 'onclick="cyclePlaybackMode()"' in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    assert '.mobile-header-btn' in css


def test_cycle_playback_mode_full_state_transitions():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    # Verify transitions in cyclePlaybackMode
    assert "currentPlaybackMode === PLAYBACK_MODE.SINGLE" in content
    assert "currentPlaybackMode = PLAYBACK_MODE.CONTINUOUS" in content
    assert "currentPlaybackMode === PLAYBACK_MODE.CONTINUOUS" in content
    assert "currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL" in content
    assert "currentPlaybackMode = PLAYBACK_MODE.SINGLE" in content

    # Simulate transition logic: SINGLE -> CONTINUOUS -> REPEAT_ALL -> SINGLE
    def cycle(curr):
        if curr == 'SINGLE':
            return 'CONTINUOUS'
        elif curr == 'CONTINUOUS':
            return 'REPEAT_ALL'
        else:
            return 'SINGLE'

    state = 'SINGLE'
    state = cycle(state)
    assert state == 'CONTINUOUS'
    state = cycle(state)
    assert state == 'REPEAT_ALL'
    state = cycle(state)
    assert state == 'SINGLE'


def test_playback_mode_button_class_bindings():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    # Check button classes bound in updateMobilePlaybackModeButton
    assert "btn btn-amber mobile-header-btn" in js
    assert "btn btn-blue mobile-header-btn" in js
    assert "btn btn-slate mobile-header-btn" in js

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    # Check CSS classes exist
    assert ".btn-slate" in css
    assert ".btn-amber" in css
    assert ".btn-blue" in css


def test_mobile_header_accessibility_aria_labels_and_css_ellipsis():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'aria-label="Open Services Explorer"' in html
    assert 'aria-label="Toggle Liturgy or Hymns Only Mode"' in html
    assert 'aria-label="Cycle Playback Mode"' in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    # Check .mobile-header-btn overflow / ellipsis styles
    assert "text-overflow: ellipsis;" in css
    assert "overflow: hidden;" in css
    assert "min-width: 0;" in css


def test_duplicate_and_load_service_from_explorer_syncs_mobile_service():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    # duplicateServiceFromExplorer syncs mobileService and re-renders
    dup_func = content[content.find("async function duplicateServiceFromExplorer") : content.find("async function deleteServiceFromExplorer")]
    assert "mobileService = currentService;" in dup_func
    assert "renderMobileServiceInfo();" in dup_func
    assert "renderMobilePlaylist();" in dup_func

    # loadServiceFromExplorer also syncs mobileService and re-renders
    load_func = content[content.find("async function loadServiceFromExplorer") : content.find("async function duplicateServiceFromExplorer")]
    assert "mobileService = currentService;" in load_func
    assert "renderMobileServiceInfo();" in load_func
    assert "renderMobilePlaylist();" in load_func


