import pytest

def test_mobile_mode_constants_present():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "const PLAYBACK_MODE" in content
    assert "SINGLE: 'SINGLE'" in content
    assert "REPEAT_ALL: 'REPEAT_ALL'" in content
    assert "const MOBILE_UI_MODE" in content
    assert "LITURGY: 'LITURGY'" in content or "SERVICE: 'SERVICE'" in content
    assert "HYMNS_ONLY: 'HYMNS_ONLY'" in content or "PRESERVICE: 'PRESERVICE'" in content
    assert "let activeCatalogTab =" in content
    assert "function getActiveDisplayItems" in content

def test_mobile_header_toggle_button_present():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert 'id="btn-mobile-mode-toggle"' in html
    assert 'toggleMobileUiMode()' in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert '.mobile-header-controls' in css
    assert '.btn-preservice-pill' in css

def test_toggle_mobile_ui_mode_function_present():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "function toggleMobileUiMode()" in content
    assert ("currentMobileUiMode = MOBILE_UI_MODE.HYMNS_ONLY" in content or
            "currentMobileUiMode = MOBILE_UI_MODE.PRESERVICE" in content)
    assert "currentPlaybackMode = PLAYBACK_MODE.REPEAT_ALL" in content
    assert "function updateMobileHeaderModeButton()" in content

def test_ended_event_listener_uses_playback_mode():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "currentPlaybackMode === PLAYBACK_MODE.SINGLE" in content
    assert "currentPlaybackMode === PLAYBACK_MODE.REPEAT_ALL" in content




