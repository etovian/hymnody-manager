# Right Panel Tabbed Interface & Template Editor Redesign

**Date**: 2026-09-05  
**Status**: Validated Design Spec  

---

## 1. Overview & Architecture

This design updates the **Hymnody Manager** desktop interface by splitting the right-hand column into two tabbed views:
1. **📋 Service Planner** (`#tab-service-planner`): Building, managing, and exporting specific dated worship service plans.
2. **⚙️ Template Editor** (`#tab-template-editor`): Creating, editing, and managing reusable setting templates (liturgical presets like DS1–DS5, Matins, Vespers, or custom templates).

This creates UI symmetry between the left-hand panel (**🎵 Hymns** / **📜 Liturgy** tabs) and the right-hand panel (**📋 Service Planner** / **⚙️ Template Editor** tabs).

---

## 2. Right-Hand Panel Components

### Tab 1: 📋 Service Planner
* Retains the current worship planning view for date-specific services.
* Contains metadata controls (Date, Liturgical Day, Setting Preset), rubric conformance badge, item list, transport/player bar, and service management buttons (`Save Service`, `Services Explorer`, `Export Mobile Zip`, `New Service`).

### Tab 2: ⚙️ Template Editor
* Embedded workspace replacing the old popup template editor modal.
* Displays an **Active Template Banner** at the top showing the template currently loaded for editing (e.g., *Editing Template: Divine Service 2 [Built-in]*).
* Includes a prominent **`📂 Select / Change Template`** button that opens the **Template Selector Modal**.
* Full form for editing template metadata (*Template Name*, *Description*) and slot arrangements.
* Quick slot additions: `+ Hymn Placeholder` and `+ Custom Slot`.
* Reorderable drag-and-drop slot cards with sequence numbers, drag handles `⋮⋮`, editable slot names, match term badges (*📖 Hymn Placeholder* vs. *🎵 Audio: Match Term*), and delete slot buttons (`✕`).
* Drag-and-Drop integration: Users can drag any track from the left-hand panel (**🎵 Hymns** or **📜 Liturgy**) directly onto template slots to bind audio, or onto empty space to append new slots.
* Footer actions: **`💾 Save Template`** and **`🗑️ Delete Template`** (for custom templates).

---

## 3. Template Selector Modal (`#template-selector-modal`)

* Opened via **`📂 Select / Change Template`** in Tab 2.
* Header: Title *"📂 Select Worship Service Template"* and a **`➕ Create New Blank Template`** action button.
* Body: Grid of template cards for all available templates (`GET /api/templates`):
  * **Card Details**: Name, type badge (*Built-in* vs. *Custom*), description, slot count.
  * **`Select for Editing`** button: Loads the selected template into Tab 2 and closes the modal.
  * **`📋 Duplicate`** button: Creates an editable copy named `[Name] (Copy)` as a new custom template.

---

## 4. Data Flow & Integration

* State management via frontend `selectedTemplateForEdit` object.
* Endpoints used:
  * `GET /api/templates`: List all templates with items.
  * `POST /api/templates`: Create new custom template.
  * `PUT /api/templates/{id}`: Update existing template.
  * `DELETE /api/templates/{id}`: Delete custom template.
* Saving or deleting a template updates `availableTemplates`, re-populates the Template Selector Modal cards, and updates the `#preset-select` dropdown in Tab 1 so new or modified templates can immediately be used for service planning.

---

## 5. Verification & Testing

* **Backend Unit & Integration Tests**: Verify template CRUD in `tests/test_services.py` and `tests/test_api.py`.
* **Frontend E2E Tests**: Update `tests/test_e2e.py` to cover tab switching, opening the Template Selector Modal, selecting/duplicating templates, dragging audio onto template slots, and saving templates.
