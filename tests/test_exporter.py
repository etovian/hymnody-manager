import io
import zipfile
import pytest
from src.database import init_db, save_hymns
from src.services import create_service_from_preset, get_service_details, update_service_items
from src.exporter import export_service_zip, generate_export_filename
from src.config import DEFAULT_MUSIC_DIR

def test_generate_export_filename_with_liturgical_day():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': 'DS3',
        'liturgical_day': 'Pentecost 15'
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_DS3_Pentecost_15.zip"

def test_generate_export_filename_without_liturgical_day():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': 'Matins',
        'liturgical_day': ''
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_Matins.zip"

def test_generate_export_filename_sanitization():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': 'DS 3 / Special',
        'liturgical_day': 'Trinity: 15th Sunday!'
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_DS_3_Special_Trinity_15th_Sunday.zip"

def test_generate_export_filename_invalid_date_fallback():
    import datetime
    today_str = datetime.date.today().strftime('%Y%m%d')
    service = {
        'service_date': 'invalid-date',
        'setting_preset': 'Vespers',
        'liturgical_day': None
    }
    filename = generate_export_filename(service)
    assert filename == f"{today_str}_Vespers.zip"

def test_generate_export_filename_preset_fallback():
    service = {
        'service_date': '2026-09-01',
        'setting_preset': None,
        'liturgical_day': ''
    }
    filename = generate_export_filename(service)
    assert filename == "20260901_Service.zip"

def test_export_service_zip(tmp_path):
    db_path = str(tmp_path / "export_test.db")
    init_db(db_path)
    
    sample_file = str(DEFAULT_MUSIC_DIR / '1-01 331 - The advent of our King.m4a')
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
    details = get_service_details(srv_id, db_path=db_path)
    items = details['items']
    items[0]['file_path'] = sample_file
    items[0]['item_title'] = "The advent of our King"
    update_service_items(srv_id, items, db_path=db_path)
    
    zip_bytes, filename = export_service_zip(srv_id, db_path=db_path)
    assert zip_bytes is not None
    assert filename == "20260830_DS2.zip"
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "00_20260830_DS2.m3u" in names
        assert "playlist.m3u" not in names
        assert any(n.endswith(".m4a") for n in names)
        
        m3u_content = zf.read("00_20260830_DS2.m3u").decode("utf-8")
        assert "#EXTM3U" in m3u_content

def test_export_service_zip_preserves_track_numbering_for_missing_files(tmp_path):
    db_path = str(tmp_path / "test_export_seq.db")
    init_db(db_path)
    
    sample_hymn = tmp_path / "1-01 331 - Test Hymn.m4a"
    sample_hymn.write_bytes(b"dummy m4a content")
    
    hymns = [
        {'id': 1, 'hymn_number': 331, 'title': 'Test Hymn 1', 'disc_number': 1, 'track_number': 1, 'file_path': str(sample_hymn), 'liturgical_season': 'General'},
        {'id': 2, 'hymn_number': 332, 'title': 'Test Hymn 3', 'disc_number': 1, 'track_number': 2, 'file_path': str(sample_hymn), 'liturgical_season': 'General'}
    ]
    save_hymns(hymns, db_path=db_path)
    
    from src.database import get_db_connection
    items = [
        {'hymn_id': 1, 'slot_name': 'Opening Hymn', 'item_title': 'Test Hymn 1', 'sequence_order': 1, 'file_path': str(sample_hymn)},
        {'hymn_id': None, 'slot_name': 'Venite', 'item_title': 'Venite (O Come)', 'sequence_order': 2, 'file_path': ''},
        {'hymn_id': 2, 'slot_name': 'Office Hymn', 'item_title': 'Test Hymn 3', 'sequence_order': 3, 'file_path': str(sample_hymn)}
    ]
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (service_date, title, setting_preset) VALUES ('2026-09-01', 'Test Matins', 'Matins')")
        s_id = cursor.lastrowid
        for it in items:
            cursor.execute("""
                INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (s_id, it['hymn_id'], it['item_title'], it['slot_name'], it['sequence_order'], it['file_path']))
        conn.commit()
        
    zip_bytes, filename = export_service_zip(s_id, db_path=db_path)
    assert zip_bytes is not None
    assert filename == "20260901_Matins.zip"
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        namelist = zf.namelist()
        assert "01_Opening_Hymn_Test_Hymn_1.m4a" in namelist
        assert "03_Office_Hymn_Test_Hymn_3.m4a" in namelist
        assert "02_Venite_Venite_(O_Come).m4a" not in namelist
        assert "00_20260901_Matins.m3u" in namelist
        assert "playlist.m3u" not in namelist
        
        m3u_content = zf.read("00_20260901_Matins.m3u").decode('utf-8')
        assert "01_Opening_Hymn_Test_Hymn_1.m4a" in m3u_content
        assert "03_Office_Hymn_Test_Hymn_3.m4a" in m3u_content

def test_export_service_zip_playlist_filename_matches_zip_base_name(tmp_path):
    db_path = str(tmp_path / "test_export_name.db")
    init_db(db_path)
    
    from src.database import get_db_connection
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO services (service_date, setting_preset, liturgical_day, title)
            VALUES ('2026-10-25', 'DS3 Common', 'Pentecost 22', 'Sunday Worship')
        """)
        s_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO service_items (service_id, item_title, slot_name, sequence_order, file_path)
            VALUES (?, 'Hymn 1', 'Opening Hymn', 1, '')
        """, (s_id,))
        conn.commit()
        
    zip_bytes, filename = export_service_zip(s_id, db_path=db_path)
    assert filename == "20261025_DS3_Common_Pentecost_22.zip"
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        namelist = zf.namelist()
        assert "00_20261025_DS3_Common_Pentecost_22.m3u" in namelist
        assert "playlist.m3u" not in namelist

def test_export_service_zip_includes_preservice_meditation_playlist(tmp_path):
    db_path = str(tmp_path / "test_preservice_export.db")
    init_db(db_path)
    
    sample_file_1 = tmp_path / "1-01 331 - Test Hymn 1.m4a"
    sample_file_1.write_bytes(b"hymn 1 content")
    sample_file_2 = tmp_path / "1-02 DS1 - Kyrie.m4a"
    sample_file_2.write_bytes(b"kyrie content")
    sample_file_3 = tmp_path / "1-03 332 - Test Hymn 2.m4a"
    sample_file_3.write_bytes(b"hymn 2 content")
    
    from src.database import get_db_connection
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (service_date, title, setting_preset) VALUES ('2026-09-12', 'Sunday Worship', 'DS1')")
        s_id = cursor.lastrowid
        cursor.execute("INSERT INTO service_items (service_id, slot_name, item_title, sequence_order, file_path, is_hymn_slot) VALUES (?, 'Opening Hymn', 'Hymn 331', 1, ?, 1)", (s_id, str(sample_file_1)))
        cursor.execute("INSERT INTO service_items (service_id, slot_name, item_title, sequence_order, file_path, is_hymn_slot) VALUES (?, 'Kyrie', 'Kyrie Ordinary', 2, ?, 0)", (s_id, str(sample_file_2)))
        cursor.execute("INSERT INTO service_items (service_id, slot_name, item_title, sequence_order, file_path, is_hymn_slot) VALUES (?, 'Closing Hymn', 'Hymn 332', 3, ?, 1)", (s_id, str(sample_file_3)))
        conn.commit()
        
    zip_bytes, filename = export_service_zip(s_id, db_path=db_path)
    assert zip_bytes is not None
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        namelist = zf.namelist()
        assert "00_20260912_DS1.m3u" in namelist
        assert "00_Preservice_Meditation.m3u" in namelist
        
        preservice_content = zf.read("00_Preservice_Meditation.m3u").decode("utf-8")
        assert "01_Opening_Hymn_Hymn_331.m4a" in preservice_content
        assert "03_Closing_Hymn_Hymn_332.m4a" in preservice_content
        assert "02_Kyrie_Kyrie_Ordinary.m4a" not in preservice_content

def test_preservice_playlist_excludes_hymn_in_ordinary_slot(tmp_path):
    db_path = str(tmp_path / "test_ordinary_hymn.db")
    init_db(db_path)
    
    hymn_933_file = tmp_path / "hymn_933.m4a"
    hymn_933_file.write_bytes(b"hymn 933 content")
    
    from src.database import get_db_connection
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (service_date, title, setting_preset) VALUES ('2026-09-12', 'Vespers', 'Vespers')")
        s_id = cursor.lastrowid
        # Hymn 933 placed into Magnificat ordinary slot (is_hymn_slot = 0)
        cursor.execute("INSERT INTO service_items (service_id, slot_name, item_title, sequence_order, file_path, is_hymn_slot) VALUES (?, 'Magnificat', 'Hymn 933 - My Soul Rejoices', 1, ?, 0)", (s_id, str(hymn_933_file)))
        conn.commit()
        
    zip_bytes, filename = export_service_zip(s_id, db_path=db_path)
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
        namelist = zf.namelist()
        assert "00_20260912_Vespers.m3u" in namelist
        if "00_Preservice_Meditation.m3u" in namelist:
            preservice_content = zf.read("00_Preservice_Meditation.m3u").decode("utf-8")
            assert "01_Magnificat_Hymn_933_-_My_Soul_Rejoices.m4a" not in preservice_content

def test_export_service_plan_json(tmp_path):
    db_path = str(tmp_path / "test_export_json.db")
    init_db(db_path)
    
    sample_file = str(tmp_path / "hymn_331.m4a")
    with open(sample_file, "wb") as f:
        f.write(b"dummy m4a audio")
        
    save_hymns([{
        'hymn_number': 331,
        'title': 'The advent of our King',
        'disc_number': 1,
        'track_number': 5,
        'album': 'The Concordia Organist',
        'artist': 'CPH',
        'year': 2009,
        'file_path': sample_file,
        'liturgical_season': 'Advent',
        'tune': 'ST. THOMAS'
    }], db_path)
    
    srv_id = create_service_from_preset("Second Sunday in Advent", "2026-12-06", "DS1", db_path=db_path)
    details = get_service_details(srv_id, db_path=db_path)
    items = details['items']
    items[0]['hymn_id'] = 1
    items[0]['file_path'] = sample_file
    items[0]['item_title'] = "The advent of our King"
    update_service_items(srv_id, items, db_path=db_path)
    
    from src.exporter import export_service_plan_json
    plan_dict = export_service_plan_json(srv_id, db_path=db_path)
    assert plan_dict is not None
    assert plan_dict["version"] == "1.0"
    assert plan_dict["service"]["title"] == "Second Sunday in Advent"
    exported_items = plan_dict["service"]["items"]
    assert len(exported_items) > 0
    hymn_item = exported_items[0]
    assert hymn_item["hymn_number"] == 331
    assert hymn_item["disc_number"] == 1
    assert hymn_item["track_number"] == 5
    assert hymn_item["album"] == "The Concordia Organist"







