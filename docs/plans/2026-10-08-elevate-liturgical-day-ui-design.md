# Elevate Liturgical Day & Remove Service Title Design Spec

**Date:** 2026-10-08  
**Status:** Approved  
**Topic:** UI / Worship Planning / Sanctuary Mode  

---

## 1. Problem Statement & Motivation

In the Hymnody Manager desktop planner and sanctuary mobile views, services displayed a redundant, uneditable title: `"Sunday Worship Service"`. This static text added visual clutter without conveying meaningful liturgical context. In Lutheran worship planning, the primary ecclesiastical identifier for a service is its **liturgical day** (e.g., *"15th Sunday after Trinity"*, *"Feast of the Epiphany"*), paired with the **service date** and **setting preset** (e.g., *"DS2"*).

This specification removes `"Sunday Worship Service"` entirely from user-facing interfaces and elevates the liturgical day into the primary heading position across desktop and mobile views, modals, and dropdowns.

---

## 2. Visual & Information Hierarchy Design

### 2.1 Desktop Service Planner Header
* **Primary Heading (`#service-title-display`):**
  * Displays `service.liturgical_day` when populated (e.g., *"15th Sunday after Trinity"*).
  * If `liturgical_day` is blank or contains only whitespace, falls back to `"${service.service_date || 'No Date'} • ${service.setting_preset || 'Service'}"`.
  * Drops the previous `"Service Plan: "` prefix.
  * Dynamically updates live when the user edits the `#liturgical-day-input` field.
* **Subtitle (`#service-subtitle-display`):**
  * Displays `Date: ${service.service_date || '--'} | Setting: ${service.setting_preset || '--'}`.
  * Removes duplicate liturgical day text previously concatenated into the subtitle.
* **Input Controls:**
  * Preserves the existing **Date**, **Setting**, and **Liturgical Day** inputs in the toolbar.

### 2.2 Sanctuary Mobile Mode Header
* **Primary Heading (`#mobile-service-title`):**
  * Formatted with prominent bold styling (`1.5rem`).
  * Displays `mobileService.liturgical_day` if present, falling back to `"${mobileService.service_date || 'No Date'} • ${mobileService.setting_preset || 'Service'}"`.
* **Subtitle (`#mobile-service-subtitle`):**
  * Displays `Date: ${mobileService.service_date || '--'} | Setting: ${mobileService.setting_preset || '--'} • ${modeBadge}` (e.g., `Date: 2026-10-11 | Setting: DS2 • Liturgy`).
  * Eliminates the hardcoded `"Sunday Worship Service"` and redundant liturgical day duplication.

### 2.3 Services Explorer & Selection Modals
* **Explorer Cards (`renderServicesExplorerList`):**
  * Card title (bold) displays `s.liturgical_day`, falling back to `"${s.service_date} • ${s.setting_preset}"`.
  * Subtitle displays `Date: ${s.service_date} | Setting: ${s.setting_preset}`.
  * Search bar filters against date, setting preset, and liturgical day.
* **Service Dropdowns (`buildServiceOptionsHtml` & `#mobile-service-select`):**
  * Option label format: `${s.service_date} • ${s.liturgical_day || s.setting_preset || 'Service'}`.
* **Import Plan Modal (`#import-modal-title`):**
  * Displays the plan's `liturgical_day` (or fallback) instead of `plan.title`.

---

## 3. Data & API Compatibility

* **Database Schema:**
  * The SQLite `services.title` column remains intact to maintain backward compatibility with existing rows, exports, and API consumers.
* **Default Values:**
  * When creating new local draft services or posting via REST API without a title, `title` defaults to `liturgical_day || "Worship Service"` behind the scenes.
* **Audio & Zip Exporters:**
  * Export package naming in `src/exporter.py` already derives filenames from date, setting preset, and liturgical day (e.g., `20261011_DS2_15th_Sunday_after_Trinity.zip`), requiring no breaking changes.

---

## 4. Verification & Testing

* **Automated Tests:**
  * Run existing pytest suite (`pytest -v`) to ensure no regressions in API, rubric, or exporter tests.
  * Update `tests/test_api.py` and `tests/test_services.py` if assertions expect `"Sunday Worship Service"`.
* **Manual Verification:**
  * Verify desktop planner heading renders liturgical day when present.
  * Verify fallback to date/setting when liturgical day is cleared.
  * Verify mobile sanctuary header displays liturgical day and clean subtitle.
  * Verify Services Explorer modal cards and dropdowns display liturgical day properly.
