# Drag-and-Drop Hymn Selection & Rubric Conformance Design Specification

**Date**: 2026-08-30  
**Project**: Hymnody Manager & Worship Planner  
**Target Repository**: `c:\dev\IdeaProjects\hymnody-manager`

---

## 1. Feature Overview & Intent

This feature enhances the **Hymnody Manager** service builder with dual drag-and-drop capabilities and real-time liturgical rubric validation:
1. **Catalog-to-Slot Dragging**: Planners can drag any hymn card from the left *Hymnal Catalog* panel and drop it directly onto any target slot in the *Service Plan* (e.g. *Hymn of the Day*, *Distribution 1*) to assign or replace hymns effortlessly.
2. **In-List Reordering & Removal**: Planners can drag service items up or down using drag handles (`⋮⋮`) to reorder the playlist sequence, or click `✕` to remove any item.
3. **Rubric Conformance Engine**: Automatically validates the service playlist against the selected setting preset (**DS1–DS5, Matins, Vespers**) and displays a `✓ Standard Rubric` or `⚠️ Custom Rubric` status badge with a details popover and one-click **"Restore Template"** button.

---

## 2. Technical Component Design

### HTML5 Drag and Drop Events
- **Catalog Items (`.hymn-item`)**: `draggable="true"`, `ondragstart="handleHymnDragStart(event, hymnId)"`.
- **Service Slots (`.service-item`)**: `ondragover="handleDragOver(event)"`, `ondragleave="handleDragLeave(event)"`, `ondrop="handleHymnDrop(event, targetSlotIndex)"`.
- **In-List Reorder Handles**: HTML5 drag events swap sequence orders on drop.

### Rubric Conformance Engine (`src/static/app.js`)
- `validateServiceRubric(service)`:
  - Compares `service.items` against `PRESETS[service.setting_preset]`.
  - Identifies missing required canticles.
  - Identifies out-of-sequence ordinaries.
  - Updates header badge: `✓ Standard DS2 Rubric` (green) vs `⚠️ Custom Rubric (1 modification)` (amber).
  - Renders details popover with **Restore Template** action.
