import datetime
import io
import os
import re
import zipfile
from src.services import get_service_details

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
    m3u_lines = ["#EXTM3U\n"]
    
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(service.get('items', []), start=1):
            file_path = item.get('file_path')
            raw_title = item.get('item_title', f"Track_{idx}")
            slot = item.get('slot_name', f"Slot_{idx}")
            seq_num = item.get('sequence_order', idx)
            
            clean_title = re.sub(r'[\/:*?"<>|]', '_', f"{slot}_{raw_title}").replace(' ', '_')
            track_filename = f"{seq_num:02d}_{clean_title}.m4a"
            
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=track_filename)
                m3u_lines.append(f"#EXTINF:-1,{raw_title}\n{track_filename}\n")
                
        base_name = filename[:-4] if filename.endswith('.zip') else filename
        playlist_filename = f"00_{base_name}.m3u"
        zf.writestr(playlist_filename, "".join(m3u_lines))
        
    return buf.getvalue(), filename

