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
    ],
    "DS3": [
        ("Opening Hymn", "HYMN_SLOT", "Invocation / Opening Hymn"),
        ("Kyrie", "DS3 - Kyrie", "Kyrie"),
        ("Gloria", "DS3 - Gloria in Excelsis", "Gloria in Excelsis"),
        ("Hymn of the Day", "HYMN_SLOT", "Hymn of the Day"),
        ("Offertory", "DS3 - Offertory", "Offertory"),
        ("Sanctus", "DS3 - Sanctus", "Sanctus"),
        ("Agnus Dei", "DS3 - Agnus Dei", "Agnus Dei"),
        ("Distribution 1", "HYMN_SLOT", "Distribution Hymn 1"),
        ("Nunc Dimittis", "DS3 - Nunc Dimittis", "Nunc Dimittis"),
        ("Closing Hymn", "HYMN_SLOT", "Closing Hymn")
    ],
    "DS4": [
        ("Opening Hymn", "HYMN_SLOT", "Invocation / Opening Hymn"),
        ("Kyrie", "DS4 - Kyrie", "Kyrie"),
        ("This is the Feast", "DS4 - This Is the Feast", "This is the Feast"),
        ("Hymn of the Day", "HYMN_SLOT", "Hymn of the Day"),
        ("Sanctus", "DS4 - Sanctus", "Sanctus"),
        ("Agnus Dei", "DS4 - Agnus Dei", "Agnus Dei"),
        ("Distribution 1", "HYMN_SLOT", "Distribution Hymn 1"),
        ("Nunc Dimittis", "DS4 - Nunc Dimittis", "Nunc Dimittis"),
        ("Closing Hymn", "HYMN_SLOT", "Closing Hymn")
    ],
    "DS5": [
        ("Opening Hymn", "HYMN_SLOT", "Invocation / Opening Hymn"),
        ("Kyrie", "DS5 - Kyrie", "Kyrie"),
        ("Gloria", "DS5 - Gloria in Excelsis", "Gloria in Excelsis"),
        ("Hymn of the Day", "HYMN_SLOT", "Hymn of the Day"),
        ("Sanctus", "DS5 - Sanctus", "Sanctus"),
        ("Agnus Dei", "DS5 - Agnus Dei", "Agnus Dei"),
        ("Distribution 1", "HYMN_SLOT", "Distribution Hymn 1"),
        ("Nunc Dimittis", "DS5 - Nunc Dimittis", "Nunc Dimittis"),
        ("Closing Hymn", "HYMN_SLOT", "Closing Hymn")
    ],
    "Matins": [
        ("Opening Hymn", "HYMN_SLOT", "Invocation Hymn"),
        ("Venite", "Matins - Venite", "Venite (O Come, Let Us Sing)"),
        ("Office Hymn", "HYMN_SLOT", "Office Hymn"),
        ("Te Deum", "Matins - Te Deum", "Te Deum Laudamus"),
        ("Closing Hymn", "HYMN_SLOT", "Closing Hymn")
    ],
    "Vespers": [
        ("Opening Hymn", "HYMN_SLOT", "Opening Hymn"),
        ("Office Hymn", "HYMN_SLOT", "Office Hymn"),
        ("Magnificat", "Vespers - Magnificat", "Magnificat (My Soul Magnifies the Lord)"),
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

def update_service_items(service_id, items_list, db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM service_items WHERE service_id = ?", (service_id,))
        for idx, item in enumerate(items_list, start=1):
            cursor.execute("""
                INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                service_id,
                item.get('hymn_id'),
                item.get('item_title', f"Item {idx}"),
                item.get('slot_name', 'Slot'),
                idx,
                item.get('file_path', '')
            ))
        conn.commit()

def list_services(db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services ORDER BY service_date DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
