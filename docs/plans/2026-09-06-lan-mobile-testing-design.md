# Design Specification — LAN Mobile Device Testing & Sanctuary Mobile Mode Auto-Detection

**Date**: 2026-09-06  
**Status**: Approved  
**Target Feature**: Sanctuary Mobile Mode LAN Device Testing & Responsive Auto-Detection

---

## 1. Overview & Objectives

To enable seamless testing and real-time sanctuary use of **Sanctuary Mobile Mode** from smartphones and tablets connected to the same local Wi-Fi network as the development machine, this design introduces:
1. An automated server launcher script (`run_server.py`) that detects the machine's local LAN IP address, generates an ASCII QR code in the terminal, and binds Uvicorn to `0.0.0.0:8000`.
2. Automatic client-side viewport and touch detection in `src/static/app.js` so mobile devices landing on the web application automatically launch in Sanctuary Mobile Mode.
3. Manual override persistence using `localStorage` to allow users to switch between Desktop Planner and Sanctuary Mobile Mode seamlessly.

---

## 2. Server Launcher (`run_server.py`)

### 2.1 Local IP Resolution & QR Code Generation
- **IP Detection**: Uses Python's standard `socket` module to create a dummy UDP connection to a public IP target (e.g., `8.8.8.8:80`) to discover the machine's active local interface IP (e.g. `192.168.1.50`).
- **QR Code Rendering**: Employs `qrcode` library to render a high-contrast QR code directly into stdout representing `http://<LAN_IP>:8000`.
- **Fallback**: If no active LAN interface is detected, falls back to `127.0.0.1` with a warning message.

### 2.2 Uvicorn Binding
- Invokes `uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)`.
- Displays Windows Firewall tips if inbound port 8000 connections time out.

---

## 3. Frontend Mobile Auto-Detection & View Switcher (`src/static/app.js`)

### 3.1 Initial Viewport & Touch Detection
- On `DOMContentLoaded`, checks:
  - `window.innerWidth < 768`
  - `window.matchMedia("(pointer: coarse)").matches`
- If a mobile device or touch viewport is detected and no explicit user preference is stored, `switchView('mobile')` is triggered automatically.

### 3.2 View Preference Persistence
- Toggling views saves `hymnody_preferred_view` (`'mobile'` or `'desktop'`) to `localStorage`.
- Explicit user selection overrides automatic viewport detection on future reloads.

---

## 4. Testing & Verification

1. **Unit Testing (`tests/test_launcher.py`)**:
   - Verify IP detection logic and Uvicorn argument configuration.
2. **Frontend Testing (`tests/test_e2e.py` / JS unit tests)**:
   - Validate viewport width detection and `localStorage` preference loading.
3. **Manual Verification**:
   - Run `python run_server.py`, scan QR code using an actual mobile device on LAN, verify instant redirection to Sanctuary Mobile Mode and HTTP 206 audio playback functionality.
