# Hymnody Manager Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local Python web application (FastAPI + SQLite + HTML5 Web UI) for Lutheran hymn metadata extraction, worship service planning (DS1–DS5 presets), sanctuary audio playback, and mobile package export (.zip + .m3u).

**Architecture:** A FastAPI backend uses custom MP4 atom parsing to index `.m4a` metadata into SQLite (`hymnody.db`), serving REST endpoints for hymn search, Divine Service templates, HTTP 206 range-request streaming, and `.zip` playlist generation. The frontend provides a desktop planning UI and a touch-friendly Sanctuary Mobile Mode.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, SQLite3, HTML5/Vanilla JS/CSS, pytest, zipfile.

---

### Task 1: Project Setup & Environment Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_setup.py`

**Step 1: Write failing setup test**

```python
# tests/test_setup.py
def test_environment_imports():
    import fastapi
    import uvicorn
    import sqlite3
    import pytest
    assert fastapi.__version__ is not None
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_setup.py -v`  
Expected: FAIL (fastapi not installed or test directory missing)

**Step 3: Write dependencies & minimal setup**

Create `requirements.txt`:
```
fastapi>=0.100.0
uvicorn>=0.22.0
pytest>=7.0.0
requests>=2.31.0
```

Install requirements into python virtual environment or system Python.

**Step 4: Run test to verify pass**

Run: `pytest tests/test_setup.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add requirements.txt src/__init__.py tests/__init__.py tests/test_setup.py
git commit -m "chore: initial project setup and dependencies"
```

---

### Task 2: MP4 Metadata Extractor Module

**Files:**
- Create: `src/scanner.py`
- Test: `tests/test_scanner.py`

**Step 1: Write failing test for MP4 atom metadata parser**

```python
# tests/test_scanner.py
import os
from src.scanner import parse_hymn_file, scan_hymns_directory

def test_parse_hymn_file_sample():
    sample_path = r'c:\dev\IdeaProjects\hymnody-manager\hymns\1-01 331 - The advent of our King.m4a'
    assert os.path.exists(sample_path)
    
    meta = parse_hymn_file(sample_path)
    assert meta['hymn_number'] == 331
    assert "The advent of our King" in meta['title']
    assert meta['disc_number'] == 1
    assert meta['track_number'] == 1
    assert meta['album'] == "The Concordia Organist"
    assert meta['artist'] == "Concordia Publishing House"
    assert meta['year'] == 2009
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_scanner.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.scanner'`

**Step 3: Implement MP4 metadata parser & directory scanner in `src/scanner.py`**

```python
# src/scanner.py
import os
import glob
import re
import struct

def parse_mp4_atoms(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    def scan_atoms(offset, end):
        atoms = []
        curr = offset
        while curr + 8 <= end:
            length = struct.unpack('>I', data[curr:curr+4])[0]
            name = data[curr+4:curr+8].decode('latin-1', errors='ignore')
            if length == 1:
                length = struct.unpack('>Q', data[curr+8:curr+16])[0]
                hdr_size = 16
            elif length == 0:
                length = end - curr
                hdr_size = 8
            else:
                hdr_size = 8
            if length < hdr_size or curr + length > end:
                break
            atoms.append((name, curr, length, hdr_size))
            curr += length
        return atoms

    root_atoms = scan_atoms(0, len(data))
    moov = next((a for a in root_atoms if a[0] == 'moov'), None)
    if not moov:
        return {}
    
    moov_sub = scan_atoms(moov[1] + moov[3], moov[1] + moov[2])
    udta = next((a for a in moov_sub if a[0] == 'udta'), None)
    
    if udta:
        sub = scan_atoms(udta[1] + udta[3], udta[1] + udta[2])
        meta = next((a for a in sub if a[0] == 'meta'), None)
    else:
        meta = next((a for a in moov_sub if a[0] == 'meta'), None)
        
    if not meta:
        return {}
        
    meta_offset = meta[1] + meta[3]
    if data[meta_offset:meta_offset+4] == b'\x00\x00\x00\x00':
        meta_offset += 4
    
    meta_sub = scan_atoms(meta_offset, meta[1] + meta[2])
    ilst = next((a for a in meta_sub if a[0] == 'ilst'), None)
    if not ilst:
        return {}
        
    tags = scan_atoms(ilst[1] + ilst[3], ilst[1] + ilst[2])
    parsed = {}
    for tag_name, t_off, t_len, t_hdr in tags:
        tag_sub = scan_atoms(t_off + t_hdr, t_off + t_len)
        data_atom = next((a for a in tag_sub if a[0] == 'data'), None)
        if data_atom:
            d_start = data_atom[1] + data_atom[3]
            type_code = struct.unpack('>I', data[d_start:d_start+4])[0]
            raw_val = data[d_start+8:data_atom[1]+data_atom[2]]
            if type_code == 1:
                val = raw_val.decode('utf-8', errors='ignore')
            elif tag_name in ('trkn', 'disk') and len(raw_val) >= 6:
                val = f"{struct.unpack('>H', raw_val[2:4])[0]}/{struct.unpack('>H', raw_val[4:6])[0]}"
            else:
                val = raw_val.decode('utf-8', errors='ignore')
            parsed[tag_name] = val
    return parsed

def parse_hymn_file(filepath):
    filename = os.path.basename(filepath)
    raw_tags = parse_mp4_atoms(filepath)
    
    # Extract Title, Disc, Track, Album, Artist, Year
    raw_title = raw_tags.get('©nam', filename.replace('.m4a', ''))
    album = raw_tags.get('©alb', 'The Concordia Organist')
    artist = raw_tags.get('©ART', 'Concordia Publishing House')
    year_str = raw_tags.get('©day', '2009')
    try:
        year = int(year_str)
    except ValueError:
        year = 2009
        
    # Disc & Track from metadata or filename
    disc_num, track_num = 1, 1
    if 'disk' in raw_tags:
        try:
            disc_num = int(raw_tags['disk'].split('/')[0])
        except Exception:
            pass
    if 'trkn' in raw_tags:
        try:
            track_num = int(raw_tags['trkn'].split('/')[0])
        except Exception:
            pass
            
    # Filename fallback regex: "1-01 331 - The advent of our King.m4a" or "30-01 DS1 - Kyrie_ Intonation.m4a"
    fn_match = re.match(r'^(\d+)-(\d+)\s+(?:(\d+)\s*-\s*)?(.+?)\.m4a$', filename)
    hymn_number = None
    title = raw_title
    
    if fn_match:
        disc_num = int(fn_match.group(1))
        track_num = int(fn_match.group(2))
        if fn_match.group(3):
            hymn_number = int(fn_match.group(3))
        title = fn_match.group(4).strip()
    elif ' - ' in raw_title and raw_title.split(' - ')[0].isdigit():
        hymn_number = int(raw_title.split(' - ')[0])
        title = ' - '.join(raw_title.split(' - ')[1:])
        
    # Determine season based on hymn number range (LSB standard index)
    season = "General"
    if hymn_number:
        if 331 <= hymn_number <= 357:
            season = "Advent"
        elif 358 <= hymn_number <= 393:
            season = "Christmas"
        elif 394 <= hymn_number <= 417:
            season = "Epiphany"
        elif 418 <= hymn_number <= 456:
            season = "Lent"
        elif 457 <= hymn_number <= 490:
            season = "Easter"
        elif 491 <= hymn_number <= 503:
            season = "Pentecost / Holy Spirit"
        elif 504 <= hymn_number <= 969:
            season = "Church Year / General"

    return {
        'file_path': filepath,
        'filename': filename,
        'title': title,
        'hymn_number': hymn_number,
        'disc_number': disc_num,
        'track_number': track_num,
        'album': album,
        'artist': artist,
        'year': year,
        'liturgical_season': season
    }

def scan_hymns_directory(directory_path):
    files = glob.glob(os.path.join(directory_path, '*.m4a'))
    results = []
    for f in files:
        try:
            parsed = parse_hymn_file(f)
            results.append(parsed)
        except Exception as e:
            print(f"Error parsing {f}: {e}")
    return results
```

**Step 4: Run test to verify pass**

Run: `pytest tests/test_scanner.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/scanner.py tests/test_scanner.py
git commit -m "feat: implement MP4 metadata parsing and filename scanning"
```

---

### Task 3: Database & Data Repository Layer

**Files:**
- Create: `src/database.py`
- Test: `tests/test_database.py`

**Step 1: Write failing test for database initialization & CRUD**

```python
# tests/test_database.py
import pytest
import os
from src.database import init_db, save_hymns, search_hymns, get_db_connection

def test_db_init_and_hymns_crud(tmp_path):
    db_path = str(tmp_path / "test_hymnody.db")
    init_db(db_path)
    
    sample_hymns = [
        {
            'hymn_number': 331,
            'title': 'The advent of our King',
            'disc_number': 1,
            'track_number': 1,
            'album': 'The Concordia Organist',
            'artist': 'Concordia Publishing House',
            'year': 2009,
            'file_path': '/hymns/1-01 331.m4a',
            'liturgical_season': 'Advent'
        }
    ]
    save_hymns(sample_hymns, db_path)
    
    results = search_hymns(query="advent", db_path=db_path)
    assert len(results) == 1
    assert results[0]['hymn_number'] == 331
    assert results[0]['title'] == 'The advent of our King'
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_database.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.database'`

**Step 3: Implement SQLite repository in `src/database.py`**

```python
# src/database.py
import sqlite3
import os

DEFAULT_DB_PATH = "hymnody.db"

def get_db_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hymns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hymn_number INTEGER,
                title TEXT NOT NULL,
                disc_number INTEGER NOT NULL,
                track_number INTEGER NOT NULL,
                album TEXT,
                artist TEXT,
                year INTEGER,
                file_path TEXT NOT NULL UNIQUE,
                liturgical_season TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_date TEXT NOT NULL,
                title TEXT NOT NULL,
                setting_preset TEXT,
                liturgical_color TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                hymn_id INTEGER,
                item_title TEXT NOT NULL,
                slot_name TEXT NOT NULL,
                sequence_order INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
                FOREIGN KEY (hymn_id) REFERENCES hymns(id)
            );
        """)
        conn.commit()

def save_hymns(hymns_list, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        for h in hymns_list:
            cursor.execute("""
                INSERT OR REPLACE INTO hymns 
                (hymn_number, title, disc_number, track_number, album, artist, year, file_path, liturgical_season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                h.get('hymn_number'),
                h.get('title'),
                h.get('disc_number', 1),
                h.get('track_number', 1),
                h.get('album', 'The Concordia Organist'),
                h.get('artist', 'Concordia Publishing House'),
                h.get('year', 2009),
                h.get('file_path'),
                h.get('liturgical_season', 'General')
            ))
        conn.commit()

def search_hymns(query=None, season=None, disc=None, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM hymns WHERE 1=1"
        params = []
        
        if query:
            if query.isdigit():
                sql += " AND (hymn_number = ? OR title LIKE ?)"
                params.extend([int(query), f"%{query}%"])
            else:
                sql += " AND title LIKE ?"
                params.append(f"%{query}%")
                
        if season:
            sql += " AND liturgical_season = ?"
            params.append(season)
            
        if disc:
            sql += " AND disc_number = ?"
            params.append(int(disc))
            
        sql += " ORDER BY disc_number ASC, track_number ASC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_hymn_by_id(hymn_id, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hymns WHERE id = ?", (hymn_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
```

**Step 4: Run test to verify pass**

Run: `pytest tests/test_database.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat: implement SQLite database schema and hymn repository CRUD"
```

---

### Task 4: FastAPI Web Server & Hymn Search/Streaming API

**Files:**
- Create: `src/main.py`
- Test: `tests/test_api.py`

**Step 1: Write failing test for FastAPI routes & HTTP Range audio streaming**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
import os
from src.main import app
from src.database import init_db, save_hymns

client = TestClient(app)

def test_api_search_and_audio_stream(tmp_path):
    db_path = str(tmp_path / "api_test.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    sample_file = r'c:\dev\IdeaProjects\hymnody-manager\hymns\1-01 331 - The advent of our King.m4a'
    save_hymns([{
        'hymn_number': 331,
        'title': 'The advent of our King',
        'disc_number': 1,
        'track_number': 1,
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'file_path': sample_file,
        'liturgical_season': 'Advent'
    }], db_path)
    
    response = client.get("/api/hymns?q=331")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    h_id = data[0]['id']
    
    # Test HTTP 206 Range Request
    stream_res = client.get(f"/api/hymns/{h_id}/audio", headers={"Range": "bytes=0-100"})
    assert stream_res.status_code in (200, 206)
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_api.py -v`  
Expected: FAIL with `ModuleNotFoundError` or endpoint 404

**Step 3: Implement FastAPI app & audio streaming in `src/main.py`**

```python
# src/main.py
import os
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from src.database import init_db, save_hymns, search_hymns, get_hymn_by_id, get_db_connection
from src.scanner import scan_hymns_directory

app = FastAPI(title="Hymnody Manager & Worship Planner")

def get_db_path():
    return os.environ.get("HYMNODY_DB_PATH", "hymnody.db")

@app.on_event("startup")
def startup_event():
    db_path = get_db_path()
    init_db(db_path)
    hymns_dir = os.environ.get("HYMNS_DIR", r"c:\dev\IdeaProjects\hymnody-manager\hymns")
    if os.path.exists(hymns_dir):
        existing = search_hymns(db_path=db_path)
        if not existing:
            scanned = scan_hymns_directory(hymns_dir)
            save_hymns(scanned, db_path=db_path)

@app.post("/api/scan")
def rescan_directory():
    db_path = get_db_path()
    hymns_dir = os.environ.get("HYMNS_DIR", r"c:\dev\IdeaProjects\hymnody-manager\hymns")
    if not os.path.exists(hymns_dir):
        raise HTTPException(status_code=404, detail="Hymns directory not found")
    scanned = scan_hymns_directory(hymns_dir)
    save_hymns(scanned, db_path=db_path)
    return {"status": "success", "count": len(scanned)}

@app.get("/api/hymns")
def get_hymns(q: str = None, season: str = None, disc: int = None):
    db_path = get_db_path()
    return search_hymns(query=q, season=season, disc=disc, db_path=db_path)

@app.get("/api/hymns/{hymn_id}")
def get_hymn(hymn_id: int):
    db_path = get_db_path()
    hymn = get_hymn_by_id(hymn_id, db_path=db_path)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return hymn

@app.get("/api/hymns/{hymn_id}/audio")
def stream_hymn_audio(hymn_id: int, request: Request):
    db_path = get_db_path()
    hymn = get_hymn_by_id(hymn_id, db_path=db_path)
    if not hymn or not os.path.exists(hymn['file_path']):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    filepath = hymn['file_path']
    file_size = os.path.getsize(filepath)
    range_header = request.headers.get('range')
    
    if not range_header:
        return FileResponse(filepath, media_type="audio/mp4")
        
    byte1, byte2 = 0, None
    m = range_header.replace('bytes=', '').split('-')
    if m[0]:
        byte1 = int(m[0])
    if len(m) > 1 and m[1]:
        byte2 = int(m[1])
        
    chunk_size = (byte2 - byte1 + 1) if byte2 else (file_size - byte1)
    
    def iterfile():
        with open(filepath, 'rb') as f:
            f.seek(byte1)
            yield f.read(chunk_size)
            
    headers = {
        'Content-Range': f'bytes {byte1}-{byte1 + chunk_size - 1}/{file_size}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(chunk_size),
        'Content-Type': 'audio/mp4',
    }
    return StreamingResponse(iterfile(), status_code=206, headers=headers)
```

**Step 4: Run test to verify pass**

Run: `pytest tests/test_api.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/main.py tests/test_api.py
git commit -m "feat: implement FastAPI endpoints and HTTP range audio streaming"
```

---

### Task 5: Divine Service Presets & Service Management

**Files:**
- Create: `src/services.py`
- Modify: `src/main.py`
- Test: `tests/test_services.py`

**Step 1: Write failing test for Divine Service preset generation & service CRUD**

```python
# tests/test_services.py
from src.database import init_db, save_hymns
from src.services import create_service_from_preset, get_service_details

def test_create_service_ds2_preset(tmp_path):
    db_path = str(tmp_path / "services_test.db")
    init_db(db_path)
    
    # Save a dummy hymn for DS2 Kyrie
    sample_file = r'c:\dev\IdeaProjects\hymnody-manager\hymns\30-30 DS2 - Kyrie_ Intonation.m4a'
    save_hymns([{
        'hymn_number': None,
        'title': 'DS2 - Kyrie_ Intonation',
        'disc_number': 30,
        'track_number': 30,
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'file_path': sample_file,
        'liturgical_season': 'Liturgical'
    }], db_path)
    
    service_id = create_service_from_preset(
        title="1st Sunday in Advent",
        service_date="2026-11-29",
        setting_preset="DS2",
        liturgical_color="Blue",
        db_path=db_path
    )
    
    assert service_id is not None
    details = get_service_details(service_id, db_path=db_path)
    assert details['title'] == "1st Sunday in Advent"
    assert len(details['items']) > 0
    assert any("Kyrie" in item['item_title'] for item in details['items'])
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_services.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.services'`

**Step 3: Implement Divine Service preset builder in `src/services.py`**

```python
# src/services.py
from src.database import get_db_connection, search_hymns

PRESETS = {
    "DS1": [
        ("Opening Hymn", "HYMN_SLOT", "Invocation / Opening Hymn"),
        ("Kyrie", "DS1 - Kyrie", "Kyrie"),
        ("Gloria", "DS1 - Gloria in Excelsis", "Gloria in Excelsis"),
        ("Collect", "DS1 - Collect of the Day", "Salutation and Collect"),
        ("Hymn of the Day", "HYMN_SLOT", "Hymn of the Day"),
        ("Offertory", "DS1 - Offertory", "Offertory"),
        ("Sanctus", "DS1 - Sanctus", "Sanctus"),
        ("Agnus Dei", "DS1 - Agnus Dei", "Agnus Dei"),
        ("Distribution 1", "HYMN_SLOT", "Distribution Hymn 1"),
        ("Nunc Dimittis", "DS1 - Nunc Dimittis", "Nunc Dimittis"),
        ("Closing Hymn", "HYMN_SLOT", "Closing Hymn")
    ],
    "DS2": [
        ("Opening Hymn", "HYMN_SLOT", "Invocation / Opening Hymn"),
        ("Kyrie", "DS2 - Kyrie", "Kyrie"),
        ("Gloria", "DS2 - Gloria in Excelsis", "Gloria in Excelsis"),
        ("Collect", "DS2 - Collect of the Day", "Salutation and Collect"),
        ("Hymn of the Day", "HYMN_SLOT", "Hymn of the Day"),
        ("Offertory", "DS2 - Offertory", "Offertory"),
        ("Sanctus", "DS2 - Sanctus", "Sanctus"),
        ("Agnus Dei", "DS2 - Agnus Dei", "Agnus Dei"),
        ("Distribution 1", "HYMN_SLOT", "Distribution Hymn 1"),
        ("Nunc Dimittis", "DS2 - Nunc Dimittis", "Nunc Dimittis"),
        ("Closing Hymn", "HYMN_SLOT", "Closing Hymn")
    ]
}

def create_service_from_preset(title, service_date, setting_preset="DS2", liturgical_color="Green", notes="", db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO services (service_date, title, setting_preset, liturgical_color, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (service_date, title, setting_preset, liturgical_color, notes))
        service_id = cursor.lastrowid
        
        preset_slots = PRESETS.get(setting_preset, PRESETS["DS2"])
        for idx, (slot_name, match_term, item_title) in enumerate(preset_slots, start=1):
            hymn_id = None
            file_path = ""
            if match_term != "HYMN_SLOT":
                # Find matching canticle track
                matches = search_hymns(query=match_term, db_path=db_path)
                if matches:
                    hymn_id = matches[0]['id']
                    file_path = matches[0]['file_path']
                    item_title = matches[0]['title']
            
            cursor.execute("""
                INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (service_id, hymn_id, item_title, slot_name, idx, file_path))
        conn.commit()
        return service_id

def get_service_details(service_id, db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        srv = cursor.fetchone()
        if not srv:
            return None
        service_dict = dict(srv)
        
        cursor.execute("SELECT * FROM service_items WHERE service_id = ? ORDER BY sequence_order ASC", (service_id,))
        items = [dict(r) for r in cursor.fetchall()]
        service_dict['items'] = items
        return service_dict
```

**Step 4: Add Service Routes to `src/main.py` & run pytest**

```python
# Add routes in src/main.py
from src.services import create_service_from_preset, get_service_details

@app.post("/api/services")
def api_create_service(payload: dict):
    db_path = get_db_path()
    s_id = create_service_from_preset(
        title=payload.get('title', 'Sunday Service'),
        service_date=payload.get('service_date', '2026-08-30'),
        setting_preset=payload.get('setting_preset', 'DS2'),
        liturgical_color=payload.get('liturgical_color', 'Green'),
        notes=payload.get('notes', ''),
        db_path=db_path
    )
    return get_service_details(s_id, db_path=db_path)

@app.get("/api/services/{service_id}")
def api_get_service(service_id: int):
    db_path = get_db_path()
    srv = get_service_details(service_id, db_path=db_path)
    if not srv:
        raise HTTPException(status_code=404, detail="Service not found")
    return srv
```

Run: `pytest tests/test_services.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/services.py src/main.py tests/test_services.py
git commit -m "feat: implement Divine Service presets and service item ordering"
```

---

### Task 6: Mobile Package Exporter (.zip + .m3u)

**Files:**
- Create: `src/exporter.py`
- Modify: `src/main.py`
- Test: `tests/test_exporter.py`

**Step 1: Write failing test for Zip Exporter**

```python
# tests/test_exporter.py
import zipfile
import io
from src.database import init_db, save_hymns
from src.services import create_service_from_preset
from src.exporter import export_service_zip

def test_export_service_zip(tmp_path):
    db_path = str(tmp_path / "export_test.db")
    init_db(db_path)
    
    sample_file = r'c:\dev\IdeaProjects\hymnody-manager\hymns\1-01 331 - The advent of our King.m4a'
    save_hymns([{
        'hymn_number': 331,
        'title': 'The advent of our King',
        'disc_number': 1,
        'track_number': 1,
        'album': 'The Concordia Organist',
        'artist': 'Concordia Publishing House',
        'year': 2009,
        'file_path': sample_file,
        'liturgical_season': 'Advent'
    }], db_path)
    
    srv_id = create_service_from_preset("Test Service", "2026-08-30", "DS2", db_path=db_path)
    
    zip_bytes = export_service_zip(srv_id, db_path=db_path)
    assert zip_bytes is not None
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "playlist.m3u" in names
        assert any(n.endswith(".m4a") for n in names)
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_exporter.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'src.exporter'`

**Step 3: Implement Zip & M3U Exporter in `src/exporter.py`**

```python
# src/exporter.py
import zipfile
import io
import os
import re
from src.services import get_service_details

def export_service_zip(service_id, db_path="hymnody.db"):
    service = get_service_details(service_id, db_path=db_path)
    if not service:
        return None
        
    buf = io.BytesIO()
    m3u_lines = ["#EXTM3U\n"]
    
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(service.get('items', []), start=1):
            file_path = item.get('file_path')
            raw_title = item.get('item_title', f"Track {idx}")
            clean_title = re.sub(r'[\/:*?"<>|]', '_', raw_title)
            filename = f"{idx:02d}_{clean_title}.m4a"
            
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=filename)
                m3u_lines.append(f"#EXTINF:-1,{raw_title}\n{filename}\n")
                
        zf.writestr("playlist.m3u", "".join(m3u_lines))
        
    return buf.getvalue()
```

**Step 4: Add Export Route in `src/main.py` & run pytest**

```python
# In src/main.py
from fastapi.responses import Response
from src.exporter import export_service_zip

@app.get("/api/services/{service_id}/export/zip")
def api_export_service_zip(service_id: int):
    db_path = get_db_path()
    zip_data = export_service_zip(service_id, db_path=db_path)
    if not zip_data:
        raise HTTPException(status_code=404, detail="Service not found or empty")
    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=service_{service_id}.zip"}
    )
```

Run: `pytest tests/test_exporter.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/exporter.py src/main.py tests/test_exporter.py
git commit -m "feat: implement mobile package zip and m3u exporter"
```

---

### Task 7: Web Frontend — Desktop Worship Builder & Sanctuary Mobile Mode

**Files:**
- Create: `src/static/index.html`
- Create: `src/static/styles.css`
- Create: `src/static/app.js`
- Test: `tests/test_frontend_assets.py`

**Step 1: Write failing test for static asset serving**

```python
# tests/test_frontend_assets.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_static_assets():
    res = client.get("/")
    assert res.status_code == 200
    assert "Hymnody Manager" in res.text
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_frontend_assets.py -v`  
Expected: FAIL

**Step 3: Implement Web Interface in `src/static/index.html`, `styles.css`, `app.js`**

Mount static directory in `src/main.py`:
```python
app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("src/static/index.html")
```

Build `index.html` featuring:
1. **Desktop Planning Mode**: Hymn search bar, season filter, Divine Service setting dropdown (DS1–DS5), drag/drop item reordering, and "Export Mobile Package (.zip)" button.
2. **Sanctuary Mobile Mode Toggle**: Switch UI to high-contrast touch controls with giant **[ PLAY ]**, **[ PAUSE ]**, **[ NEXT TRACK ]**, and **[ PREV TRACK ]** buttons for volunteer operation.

**Step 4: Run test to verify pass**

Run: `pytest tests/test_frontend_assets.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/static/index.html src/static/styles.css src/static/app.js tests/test_frontend_assets.py
git commit -m "feat: add desktop worship builder and sanctuary mobile UI"
```

---

### Task 8: End-to-End Verification & Full Test Suite

**Files:**
- Create: `tests/test_e2e.py`

**Step 1: Write comprehensive E2E test**

```python
# tests/test_e2e.py
from fastapi.testclient import TestClient
import os
from src.main import app
from src.database import init_db

client = TestClient(app)

def test_full_workflow(tmp_path):
    db_path = str(tmp_path / "e2e.db")
    os.environ["HYMNODY_DB_PATH"] = db_path
    init_db(db_path)
    
    # 1. Trigger directory scan
    scan_res = client.post("/api/scan")
    assert scan_res.status_code == 200
    assert scan_res.json()["count"] > 0
    
    # 2. Search for Advent hymns
    search_res = client.get("/api/hymns?q=331")
    assert search_res.status_code == 200
    hymns = search_res.json()
    assert len(hymns) > 0
    
    # 3. Create DS2 service plan
    srv_res = client.post("/api/services", json={
        "title": "Advent Sunday",
        "service_date": "2026-11-29",
        "setting_preset": "DS2"
    })
    assert srv_res.status_code == 200
    srv_id = srv_res.json()["id"]
    
    # 4. Export zip package
    zip_res = client.get(f"/api/services/{srv_id}/export/zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
```

**Step 2: Run full test suite**

Run: `pytest -v`  
Expected: 100% PASS

**Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add end-to-end integration test suite"
```
