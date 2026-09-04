import os
import glob
import re
import struct
from src.database import normalize_path

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
    filepath = normalize_path(filepath)
    filename = os.path.basename(filepath)
    raw_tags = parse_mp4_atoms(filepath)

    
    raw_title = raw_tags.get('©nam', filename.replace('.m4a', ''))
    album = raw_tags.get('©alb', 'The Concordia Organist')
    artist = raw_tags.get('©ART', 'Concordia Publishing House')
    year_str = raw_tags.get('©day', '2009')
    try:
        year = int(year_str)
    except ValueError:
        year = 2009
        
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
            season = "Pentecost"
        elif 590 <= hymn_number <= 605:
            season = "Baptism"
        elif 606 <= hymn_number <= 616:
            season = "Confession"
        elif 617 <= hymn_number <= 643:
            season = "Communion"
        elif 708 <= hymn_number <= 780:
            season = "Trust & Comfort"
        elif 781 <= hymn_number <= 824:
            season = "Praise"
        else:
            season = "General"
    else:
        fn = filename.lower()
        if 'ds1' in fn:
            season = "DS1"
        elif 'ds2' in fn:
            season = "DS2"
        elif 'ds3' in fn:
            season = "DS3"
        elif 'ds4' in fn:
            season = "DS4"
        elif 'ds5' in fn:
            season = "DS5"
        elif 'ma -' in fn or 'matins' in fn:
            season = "Matins"
        elif 've -' in fn or 'vespers' in fn:
            season = "Vespers"
        elif 'mp -' in fn or 'morning prayer' in fn:
            season = "Morning Prayer"
        elif 'ep -' in fn or 'evening prayer' in fn:
            season = "Evening Prayer"
        elif 'co -' in fn or 'compline' in fn:
            season = "Compline"
        elif 'pp -' in fn or 'pt -' in fn or 'psalm tone' in fn:
            season = "Psalm Tones"
        elif any(kw in fn for kw in ['kyrie', 'gloria', 'sanctus', 'agnus', 'nunc']):
            season = "Liturgical"

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
