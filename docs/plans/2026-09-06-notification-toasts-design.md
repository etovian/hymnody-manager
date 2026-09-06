# Notification Toasts Design Spec

**Date**: 2026-09-06  
**Status**: Approved  

---

## 1. Overview & Goals

This feature introduces a lightweight, non-intrusive Toast Notification Engine to **Hymnody Manager** to provide visual feedback for user actions (saving service plans, template edits, deletions, exports) and network error alerts.

---

## 2. User Experience & Placement

- **Position**: Top-right corner overlay (`top: 20px; right: 20px; z-index: 9999`).
- **Stacking Limit**: Maximum of 5 active toast cards displayed at any time. Oldest toasts are automatically pruned when a 6th notification arrives.
- **Card Design**: Dark slate theme (`#1e293b`) with left accent border, icon, title, message text, and an explicit `✕` close button:
  - 🟢 **Success**: Emerald border (`#10b981`), Checkmark icon.
  - 🔵 **Info**: Sky blue border (`#3b82f6`), Info icon.
  - 🟡 **Warning**: Amber border (`#f59e0b`), Warning triangle icon.
  - 🔴 **Error**: Red border (`#ef4444`), Error cross icon.

### Dismissal Behavior
- **Success & Info**: Auto-dismiss after 4 seconds.
- **Warning**: Auto-dismiss after 8 seconds.
- **Error**: Sticky (remains visible until the user clicks `✕`).

---

## 3. Component Architecture & JavaScript API

### HTML Container
Added inside `<body>` in `src/static/index.html`:
```html
<div id="toast-container" class="toast-container"></div>
```

### CSS Animations & Styling
Defined in `src/static/styles.css`:
- `.toast-container`: Fixed position top-right, flex-column layout.
- `.toast`: Flex layout with smooth entrance animation (`@keyframes slideInRight`) and exit animation (`@keyframes fadeOutRight`).

### JavaScript Toast API
Exposed in `src/static/app.js`:
```javascript
function showToast(message, type = 'info', title = null, duration = null)
```

---

## 4. Application Event Triggers

### Service Planner
- **Save Service**: `showToast("Service plan saved successfully", "success", "Plan Saved")`
- **Delete Service**: `showToast("Service plan deleted", "warning", "Service Deleted")`
- **New Service**: `showToast("Created new service plan", "info", "New Service")`
- **Setting Preset Change**: `showToast("Switched setting preset to DS1", "info")`

### Template Editor
- **Save Template**: `showToast("Template 'DS2 Custom' saved", "success", "Template Saved")`
- **Delete Template**: `showToast("Template removed", "warning", "Template Deleted")`
- **Create/Duplicate Template**: `showToast("Created new template", "success")`

### Exporter
- **Export Packaging**: `showToast("Generating mobile ZIP package...", "info")`
- **Export Complete**: `showToast("Mobile package downloaded successfully", "success")`
- **Missing Audio Alert**: `showToast("Package downloaded with missing audio files", "warning", "Missing Audio")`

### Global API / Network Errors
- **Fetch Errors**: `showToast("Failed to connect to backend server", "error", "API Error")`

---

## 5. Testing & Verification Plan

### Backend & API
- Verify via `pytest -v` that all backend CRUD endpoints return standard HTTP responses.

### Manual UI Verification
1. Save service plan -> verify emerald toast appears top-right and auto-dismisses after 4s.
2. Delete service plan -> verify amber toast appears ("Service plan deleted").
3. Save template / delete template -> verify appropriate toasts trigger.
4. Export Mobile ZIP -> verify progress info toast followed by success/warning toast.
5. Trigger API error -> verify sticky red error toast requires manual close (`✕`).
6. Trigger >5 rapid notifications -> verify stack auto-removes the oldest toast.
