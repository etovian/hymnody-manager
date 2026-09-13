import pytest

def test_mobile_mode_constants_present():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "const PLAYBACK_MODE" in content
    assert "SINGLE: 'SINGLE'" in content
    assert "REPEAT_ALL: 'REPEAT_ALL'" in content
    assert "const MOBILE_UI_MODE" in content
    assert "SERVICE: 'SERVICE'" in content
    assert "PRESERVICE: 'PRESERVICE'" in content
    assert "function getActiveDisplayItems()" in content

def test_mobile_header_toggle_button_present():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert 'id="btn-mobile-mode-toggle"' in html
    assert 'toggleMobileUiMode()' in html

    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert '.mobile-header-controls' in css
    assert '.btn-preservice-pill' in css

