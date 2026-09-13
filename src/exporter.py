import datetime
import io
import os
import re
import zipfile
from src.services import get_service_details

from src.database import get_hymn_by_id

def generate_export_filename(service: dict) -> str:
    date_str = (service.get('service_date') or '').strip()
    digits = ''.join(c for c in date_str if c.isdigit())
    if len(digits) != 8:
        digits = datetime.date.today().strftime('%Y%m%d')
        
    preset = service.get('setting_preset') or ''
    clean_preset = re.sub(r'[^\w]', '_', str(preset))
    clean_preset = re.sub(r'_+', '_', clean_preset).strip('_')
    if not clean_preset:
        clean_preset = 'Service'
        
    lit_day = service.get('liturgical_day') or ''
    clean_lit_day = re.sub(r'[^\w]', '_', str(lit_day))
    clean_lit_day = re.sub(r'_+', '_', clean_lit_day).strip('_')
    
    parts = [digits, clean_preset]
    if clean_lit_day:
        parts.append(clean_lit_day)
        
    base_name = '_'.join(parts)
    return f"{base_name}.zip"

def export_service_zip(service_id: int, db_path: str = "hymnody.db") -> tuple[bytes | None, str | None]:
    service = get_service_details(service_id, db_path=db_path)
    if not service:
        return None, None
        
    filename = generate_export_filename(service)
    buf = io.BytesIO()
    main_m3u_lines = ["#EXTM3U\n"]
    preservice_m3u_lines = ["#EXTM3U\n"]
    
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(service.get('items', []), start=1):
            file_path = item.get('file_path')
            raw_title = item.get('item_title', f"Track_{idx}")
            slot = item.get('slot_name', f"Slot_{idx}")
            seq_num = item.get('sequence_order', idx)
            
            clean_title = re.sub(r'[\/:*?"<>|]', '_', f"{slot}_{raw_title}").replace(' ', '_')
            track_filename = f"{seq_num:02d}_{clean_title}.m4a"
            
            is_hymn = item.get('is_hymn_slot') == 1 or (item.get('is_hymn_slot') is None and 'hymn' in slot.lower())
            
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=track_filename)
                entry = f"#EXTINF:-1,{raw_title}\n{track_filename}\n"
                main_m3u_lines.append(entry)
                if is_hymn:
                    preservice_m3u_lines.append(entry)
                
        base_name = filename[:-4] if filename.endswith('.zip') else filename
        playlist_filename = f"00_{base_name}.m3u"
        zf.writestr(playlist_filename, "".join(main_m3u_lines))
        if len(preservice_m3u_lines) > 1:
            zf.writestr("00_Preservice_Meditation.m3u", "".join(preservice_m3u_lines))
        
    return buf.getvalue(), filename

def export_service_plan_json(service_id: int, db_path: str = "hymnody.db") -> dict | None:
    service = get_service_details(service_id, db_path=db_path)
    if not service:
        return None
        
    items = []
    for item in service.get('items', []):
        hymn_id = item.get('hymn_id')
        hymn_info = get_hymn_by_id(hymn_id, db_path=db_path) if hymn_id else None

        hymn_num = item.get('hymn_number')
        if hymn_num is None and hymn_info:
            hymn_num = hymn_info.get('hymn_number')

        disc_num = item.get('disc_number')
        if disc_num is None and hymn_info:
            disc_num = hymn_info.get('disc_number')

        track_num = item.get('track_number')
        if track_num is None and hymn_info:
            track_num = hymn_info.get('track_number')

        tune_val = item.get('tune')
        if tune_val is None and hymn_info:
            tune_val = hymn_info.get('tune')

        album_val = item.get('album')
        if album_val is None and hymn_info:
            album_val = hymn_info.get('album')

        items.append({
            'slot_name': item.get('slot_name', ''),
            'item_title': item.get('item_title', ''),
            'sequence_order': item.get('sequence_order', 1),
            'is_hymn_slot': item.get('is_hymn_slot'),
            'hymn_number': hymn_num,
            'disc_number': disc_num,
            'track_number': track_num,
            'tune': tune_val,
            'album': album_val
        })
        
    return {
        "version": "1.0",
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "service": {
            "title": service.get('title', ''),
            "setting_preset": service.get('setting_preset', ''),
            "service_date": service.get('service_date', ''),
            "liturgical_day": service.get('liturgical_day', ''),
            "notes": service.get('notes', ''),
            "items": items
        }
    }



