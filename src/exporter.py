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
            raw_title = item.get('item_title', f"Track_{idx}")
            slot = item.get('slot_name', f"Slot_{idx}")
            seq_num = item.get('sequence_order', idx)
            
            clean_title = re.sub(r'[\/:*?"<>|]', '_', f"{slot}_{raw_title}").replace(' ', '_')
            filename = f"{seq_num:02d}_{clean_title}.m4a"
            
            if file_path and os.path.exists(file_path):
                zf.write(file_path, arcname=filename)
                m3u_lines.append(f"#EXTINF:-1,{raw_title}\n{filename}\n")
                
        zf.writestr("playlist.m3u", "".join(m3u_lines))
        
    return buf.getvalue()
