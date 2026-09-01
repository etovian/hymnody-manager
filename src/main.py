import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response, Body
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.database import init_db, save_hymns, search_hymns, get_hymn_by_id
from src.scanner import scan_hymns_directory
from src.services import (
    create_service_from_preset, get_service_details, update_service_items,
    list_services, validate_service_rubric, update_service_metadata,
    delete_service, duplicate_service, list_templates, get_template_by_id,
    save_template, delete_template, get_hymn_usage_analytics
)
from src.exporter import export_service_zip

def get_db_path():
    return os.environ.get("HYMNODY_DB_PATH", "hymnody.db")

def get_music_dir():
    return os.environ.get("MUSIC_DIR", r"c:\dev\IdeaProjects\hymnody-manager\music")

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = get_db_path()
    init_db(db_path)
    music_dir = get_music_dir()
    if os.path.exists(music_dir):
        existing = search_hymns(db_path=db_path)
        if not existing:
            scanned = scan_hymns_directory(music_dir)
            save_hymns(scanned, db_path=db_path)
    yield

app = FastAPI(title="Hymnody Manager & Worship Planner", lifespan=lifespan)

@app.post("/api/scan")
def rescan_directory():
    db_path = get_db_path()
    music_dir = get_music_dir()
    if not os.path.exists(music_dir):
        raise HTTPException(status_code=404, detail="Music directory not found")
    scanned = scan_hymns_directory(music_dir)
    save_hymns(scanned, db_path=db_path)
    return {"status": "success", "count": len(scanned)}

@app.get("/api/hymns")
def api_get_hymns(q: str = None, season: str = None, disc: int = None):
    db_path = get_db_path()
    return search_hymns(query=q, season=season, disc=disc, db_path=db_path)

@app.get("/api/hymns/{hymn_id}")
def api_get_hymn(hymn_id: int):
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

@app.get("/api/templates")
def api_list_templates():
    return list_templates(db_path=get_db_path())

@app.get("/api/templates/{template_id}")
def api_get_template(template_id: int):
    t = get_template_by_id(template_id, db_path=get_db_path())
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t

@app.post("/api/templates")
def api_create_template(payload: dict):
    t_id = save_template(
        name=payload.get('name'),
        description=payload.get('description', ''),
        items=payload.get('items', []),
        db_path=get_db_path()
    )
    return get_template_by_id(t_id, db_path=get_db_path())

@app.put("/api/templates/{template_id}")
def api_update_template(template_id: int, payload: dict):
    t_id = save_template(
        name=payload.get('name'),
        description=payload.get('description', ''),
        items=payload.get('items', []),
        template_id=template_id,
        db_path=get_db_path()
    )
    return get_template_by_id(t_id, db_path=get_db_path())

@app.delete("/api/templates/{template_id}")
def api_delete_template(template_id: int):
    delete_template(template_id, db_path=get_db_path())
    return {"status": "success"}

@app.get("/api/services")
def api_list_services():
    db_path = get_db_path()
    return list_services(db_path=db_path)

@app.post("/api/services")
def api_create_service(payload: dict):
    db_path = get_db_path()
    s_id = create_service_from_preset(
        title=payload.get('title', 'Sunday Service'),
        service_date=payload.get('service_date', '2026-08-30'),
        setting_preset=payload.get('setting_preset', 'DS2'),
        liturgical_color=payload.get('liturgical_color', 'Green'),
        liturgical_day=payload.get('liturgical_day', ''),
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

@app.put("/api/services/{service_id}/metadata")
def api_update_service_metadata(service_id: int, payload: dict):
    db_path = get_db_path()
    update_service_metadata(
        service_id=service_id,
        service_date=payload.get('service_date'),
        liturgical_day=payload.get('liturgical_day'),
        title=payload.get('title'),
        notes=payload.get('notes'),
        db_path=db_path
    )
    return get_service_details(service_id, db_path=db_path)

@app.post("/api/services/{service_id}/duplicate")
def api_duplicate_service(service_id: int, payload: dict = Body({})):
    db_path = get_db_path()
    new_id = duplicate_service(service_id, new_date=payload.get('new_date'), db_path=db_path)
    if not new_id:
        raise HTTPException(status_code=404, detail="Service not found")
    return get_service_details(new_id, db_path=db_path)

@app.delete("/api/services/{service_id}")
def api_delete_service(service_id: int):
    delete_service(service_id, db_path=get_db_path())
    return {"status": "success"}

@app.get("/api/services/{service_id}/rubric")
def api_get_service_rubric(service_id: int):
    db_path = get_db_path()
    return validate_service_rubric(service_id, db_path=db_path)

@app.put("/api/services/{service_id}/items")
def api_update_service_items(service_id: int, items: list = Body(...)):
    db_path = get_db_path()
    update_service_items(service_id, items, db_path=db_path)
    return get_service_details(service_id, db_path=db_path)

@app.get("/api/services/{service_id}/export/zip")
def api_export_service_zip(service_id: int):
    db_path = get_db_path()
    zip_data, filename = export_service_zip(service_id, db_path=db_path)
    if not zip_data:
        raise HTTPException(status_code=404, detail="Service not found or empty")
    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/analytics/hymns")
def api_get_hymn_analytics():
    return get_hymn_usage_analytics(db_path=get_db_path())

# Static files mount
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Hymnody Manager API is running"}

