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
