# Hymnody Manager & Worship Planner

**Hymnody Manager** is a lightweight, local Python web application designed for Lutheran worship planning, hymnody indexing, sanctuary audio streaming, and mobile playlist export.

It indexes `.m4a` accompaniment audio files (specifically *The Concordia Organist* set discs 1–31 and Divine Service 1–5 settings), stores metadata in a local SQLite database (`hymnody.db`), and provides a dual-mode browser interface: a **Desktop Worship Planner** for church leaders and a high-contrast **Sanctuary Mobile Mode** for sanctuary audio operators.

- **GitHub Repository**: [https://github.com/etovian/hymnody-manager](https://github.com/etovian/hymnody-manager)

---

## Key Features

1. **Read-Only Metadata Indexing & Deduplication**:
   - Custom binary MP4 atom parser (`src/scanner.py`) extracts titles, hymn numbers, disc/track numbers, album, artist, year, and liturgical seasons without modifying source audio files.
   - Automatic track deduplication handles suffixed duplicate files (e.g. `101_Hymn (1).m4a`), backed by a maintenance script (`scripts/cleanup_duplicates.py`).

2. **Divine Service & Daily Office Presets + Custom Template Builder**:
   - Pre-configured templates for **Divine Service 1–5 (DS1–DS5)**, **Matins**, and **Vespers** that insert liturgical ordinaries (*Kyrie*, *Gloria*, *Sanctus*, *Agnus Dei*, *Nunc Dimittis*) alongside hymn slots.
   - Interactive drag-and-drop template editor with custom template saving and alphabetized selector.

3. **Sanctuary Mobile Mode & Terminal QR Code Launcher**:
   - Automated server launcher (`run_server.py`) detects your local Wi-Fi IP address and displays a scannable **QR code** in your terminal window for instant smartphone access over your local network.
   - Automatic viewport and touch detection redirects mobile visitors directly to Sanctuary Mobile Mode.
   - High-contrast touch UI with oversized **PLAY**, **PAUSE**, and **NEXT TRACK** buttons designed for sanctuary volunteers.

4. **HTTP 206 Range Audio Streaming**:
   - FastAPI streaming endpoint supporting range requests for instant browser seeking and track jumping without downloading full audio files.

5. **Mobile Package Exporter**:
   - Generates a downloadable `.zip` package containing dynamically named audio tracks (e.g., `01_Invocation_Hymn_331.m4a`, `02_DS2_Kyrie.m4a`) and a `playlist.m3u` file for offline mobile Bluetooth playback.

---

## Quick Start & Installation

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Setup Environment
Clone the repository and install dependencies:
```bash
git clone https://github.com/etovian/hymnody-manager.git
cd hymnody-manager
pip install -r requirements.txt
```

---

## Running the Server

### Option A: LAN & Mobile Testing Launcher (Recommended)
To run the server accessible to smartphones, tablets, or laptops on your local Wi-Fi network:

```bash
python run_server.py
```

- **Terminal QR Code**: Automatically prints a QR code in the terminal window. Point your mobile phone camera at the QR code to open the application directly.
- **Local Network Binding**: Binds Uvicorn to `0.0.0.0:8000` and displays your machine's LAN URL (e.g. `http://192.168.1.50:8000`).
- **Command Line Flags**:
  - `--port <number>`: Specify custom port (default `8000`).
  - `--no-reload`: Disable development auto-reload.

> [!NOTE]
> If your mobile device cannot connect over local Wi-Fi, ensure inbound traffic on port 8000 is permitted in Windows Defender Firewall or your system firewall.

### Option B: Local Machine Only
If you only need to access the app on your local computer:

```bash
uvicorn src.main:app --reload --port 8000
```
Then open `http://localhost:8000` in your web browser.

---

## Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `HYMNODY_DB_PATH` | Path to SQLite database file | `hymnody.db` |
| `MUSIC_DIR` | Directory containing `.m4a` audio files | `c:\dev\IdeaProjects\hymnody-manager\music` |

---

## Testing & Maintenance

### Run Automated Tests
Run the full pytest suite (60+ tests):
```bash
pytest -v
```

### Audio File Deduplication Cleanup
Purge duplicate suffixed audio files (`(1).m4a`) from metadata indexing:
```bash
# Dry run (inspection only):
python scripts/cleanup_duplicates.py --dry-run

# Execute purge:
python scripts/cleanup_duplicates.py --apply
```

---

## Project Structure

```
hymnody-manager/
├── music/                  # Read-only audio directory (.m4a)
├── docs/                   # Specifications, architecture plans, and reports
├── scripts/
│   └── cleanup_duplicates.py # Maintenance script to purge duplicate tracks
├── src/
│   ├── scanner.py          # MP4 atom metadata parser & deduplication engine
│   ├── database.py         # SQLite schema initialization, migrations & repository
│   ├── services.py         # Liturgical presets, template builder & rubric validator
│   ├── exporter.py         # Mobile zip package & m3u generator
│   ├── main.py             # FastAPI REST endpoints & HTTP 206 range streamer
│   └── static/             # Vanilla HTML5, CSS & JS frontend assets
├── tests/                  # Automated pytest test suite
├── run_server.py           # LAN server launcher with terminal QR code
├── requirements.txt        # Python dependencies
└── GEMINI.md               # Developer and AI assistant guide
```

---

## License

MIT License. Designed for Lutheran church sanctuary organist support and worship planning.
