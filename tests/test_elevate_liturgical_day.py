import pytest

def test_index_html_no_static_sunday_worship_service():
    with open("src/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert "Sunday Worship Service" not in html
    assert "Service Plan: Loading..." not in html
    assert 'id="service-title-display"' in html
    assert 'id="mobile-service-title"' in html

def test_app_js_service_heading_helper():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "function getServiceHeading(" in js
    assert "service.liturgical_day" in js
    assert "service.service_date" in js
    assert "service.setting_preset" in js

def test_app_js_desktop_header_elevation():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "getServiceHeading(service)" in js
    assert "Service Plan: ${service.title" not in js

def test_app_js_mobile_header_elevation():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "getServiceHeading(mobileService)" in js
    assert "mobileService.title || 'Sunday Service'" not in js

def test_app_js_subtitles_no_duplicate_liturgical_day():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    # Assert old duplication pattern is removed
    assert "${service.liturgical_day ? ' • ' + service.liturgical_day : ''}" not in js
    assert "${mobileService.liturgical_day ? ' • ' + mobileService.liturgical_day : ''}" not in js
    # Assert simplified subtitle format is present
    assert "Date: ${service.service_date" in js
    assert "Date: ${mobileService.service_date" in js

def test_app_js_explorer_and_dropdown_elevation():
    with open("src/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "getServiceHeading(s)" in js
    assert "Sunday Worship Service" not in js
