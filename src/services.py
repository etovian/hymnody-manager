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
        ("Collect", "DS3 - Collect of the Day", "Salutation and Collect"),
        ("Collect Amen", "DS3 - Collect Amen", "Collect Amen"),
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

def seed_templates_if_empty(db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM service_templates")
        if cursor.fetchone()['count'] > 0:
            return
        
        for name, slots in PRESETS.items():
            cursor.execute("""
                INSERT INTO service_templates (name, description, is_builtin)
                VALUES (?, ?, 1)
            """, (name, f"Standard Lutheran Service Book preset {name}"))
            template_id = cursor.lastrowid
            
            for idx, (slot_name, match_term, item_title) in enumerate(slots, start=1):
                is_hymn = 1 if match_term == "HYMN_SLOT" else 0
                cursor.execute("""
                    INSERT INTO template_items (template_id, slot_name, match_term, item_title, sequence_order, is_hymn_slot)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (template_id, slot_name, match_term, item_title, idx, is_hymn))
        conn.commit()

def list_templates(db_path="hymnody.db"):
    seed_templates_if_empty(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM service_templates ORDER BY is_builtin DESC, name ASC")
        templates = [dict(r) for r in cursor.fetchall()]
        for t in templates:
            cursor.execute("SELECT * FROM template_items WHERE template_id = ? ORDER BY sequence_order ASC", (t['id'],))
            t['items'] = [dict(r) for r in cursor.fetchall()]
        return templates

def get_template_by_name(name, db_path="hymnody.db"):
    seed_templates_if_empty(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM service_templates WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            return None
        t = dict(row)
        cursor.execute("SELECT * FROM template_items WHERE template_id = ? ORDER BY sequence_order ASC", (t['id'],))
        t['items'] = [dict(r) for r in cursor.fetchall()]
        return t

def get_template_by_id(template_id, db_path="hymnody.db"):
    seed_templates_if_empty(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM service_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        if not row:
            return None
        t = dict(row)
        cursor.execute("SELECT * FROM template_items WHERE template_id = ? ORDER BY sequence_order ASC", (t['id'],))
        t['items'] = [dict(r) for r in cursor.fetchall()]
        return t

def save_template(name, description="", items=None, is_builtin=0, template_id=None, db_path="hymnody.db"):
    items = items or []
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if template_id:
            cursor.execute("""
                UPDATE service_templates SET name = ?, description = ? WHERE id = ?
            """, (name, description, template_id))
            cursor.execute("DELETE FROM template_items WHERE template_id = ?", (template_id,))
        else:
            cursor.execute("""
                INSERT INTO service_templates (name, description, is_builtin) VALUES (?, ?, ?)
            """, (name, description, is_builtin))
            template_id = cursor.lastrowid

        for idx, item in enumerate(items, start=1):
            cursor.execute("""
                INSERT INTO template_items (template_id, slot_name, match_term, item_title, sequence_order, is_hymn_slot)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template_id,
                item.get('slot_name', f'Slot {idx}'),
                item.get('match_term', 'HYMN_SLOT'),
                item.get('item_title', item.get('slot_name', f'Slot {idx}')),
                idx,
                1 if item.get('match_term') == 'HYMN_SLOT' or item.get('is_hymn_slot') else 0
            ))
        conn.commit()
        return template_id

def delete_template(template_id, db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM service_templates WHERE id = ? AND is_builtin = 0", (template_id,))
        conn.commit()

def create_service_from_preset(title, service_date, setting_preset="DS2", liturgical_color="Green", liturgical_day="", notes="", db_path="hymnody.db"):
    seed_templates_if_empty(db_path)
    tmpl = get_template_by_name(setting_preset, db_path)
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO services (service_date, title, liturgical_day, setting_preset, liturgical_color, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (service_date, title, liturgical_day, setting_preset, liturgical_color, notes))
        service_id = cursor.lastrowid
        
        if tmpl and tmpl.get('items'):
            preset_slots = [(item['slot_name'], item['match_term'], item['item_title']) for item in tmpl['items']]
        else:
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

def update_service_metadata(service_id, service_date=None, liturgical_day=None, title=None, notes=None, db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        fields = []
        params = []
        if service_date is not None:
            fields.append("service_date = ?")
            params.append(service_date)
        if liturgical_day is not None:
            fields.append("liturgical_day = ?")
            params.append(liturgical_day)
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
            
        if fields:
            params.append(service_id)
            cursor.execute(f"UPDATE services SET {', '.join(fields)} WHERE id = ?", params)
            conn.commit()

def delete_service(service_id, db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM service_items WHERE service_id = ?", (service_id,))
        cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
        conn.commit()

def duplicate_service(service_id, new_date=None, db_path="hymnody.db"):
    orig = get_service_details(service_id, db_path=db_path)
    if not orig:
        return None
    date_str = new_date or orig['service_date']
    new_title = f"{orig['title']} (Copy)"
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO services (service_date, title, liturgical_day, setting_preset, liturgical_color, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_str, new_title, orig.get('liturgical_day', ''), orig.get('setting_preset', 'DS2'), orig.get('liturgical_color', 'Green'), orig.get('notes', '')))
        new_id = cursor.lastrowid
        
        for item in orig.get('items', []):
            cursor.execute("""
                INSERT INTO service_items (service_id, hymn_id, item_title, slot_name, sequence_order, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_id, item.get('hymn_id'), item.get('item_title'), item.get('slot_name'), item.get('sequence_order'), item.get('file_path', '')))
        conn.commit()
        return new_id

def list_services(db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services ORDER BY service_date DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def validate_service_rubric(service_id, db_path="hymnody.db"):
    srv = get_service_details(service_id, db_path=db_path)
    if not srv:
        return {'is_conformant': False, 'issues': ['Service not found'], 'setting': 'DS2'}
        
    setting = srv.get('setting_preset', 'DS2')
    tmpl = get_template_by_name(setting, db_path=db_path)
    
    if tmpl and tmpl.get('items'):
        expected_slots = [(item['slot_name'], item['match_term'], item['item_title']) for item in tmpl['items']]
    else:
        expected_slots = PRESETS.get(setting, PRESETS["DS2"])
        
    actual_items = srv.get('items', [])
    
    issues = []
    for slot_name, match_term, item_title in expected_slots:
        if match_term != "HYMN_SLOT":
            found = False
            for item in actual_items:
                title = item.get('item_title', '').lower()
                slot = item.get('slot_name', '').lower()
                target = slot_name.lower()
                if target in slot or target in title:
                    found = True
                    break
            if not found:
                issues.append(f"Missing required canticle: {slot_name} ({item_title})")
                
    return {
        'is_conformant': len(issues) == 0,
        'issues': issues,
        'setting': setting
    }

def get_hymn_usage_analytics(db_path="hymnody.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.id as hymn_id, h.hymn_number, h.title, h.liturgical_season,
                   COUNT(si.id) as usage_count,
                   MAX(s.service_date) as last_used_date
            FROM service_items si
            JOIN services s ON si.service_id = s.id
            JOIN hymns h ON si.hymn_id = h.id
            GROUP BY h.id
            ORDER BY usage_count DESC, last_used_date DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

