import sqlite3
import os

DEFAULT_DB_PATH = "hymnody.db"

def normalize_path(path):
    if not path:
        return ""
    norm = os.path.abspath(path).replace('/', '\\')
    if len(norm) >= 2 and norm[1] == ':':
        norm = norm[0].upper() + norm[1:]
    return norm

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
                liturgical_day TEXT,
                setting_preset TEXT,
                liturgical_color TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Check if liturgical_day column exists (migration for existing DBs)
        cursor.execute("PRAGMA table_info(services)")
        cols = [col['name'] for col in cursor.fetchall()]
        if 'liturgical_day' not in cols:
            cursor.execute("ALTER TABLE services ADD COLUMN liturgical_day TEXT")

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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_builtin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                slot_name TEXT NOT NULL,
                match_term TEXT,
                item_title TEXT NOT NULL,
                sequence_order INTEGER NOT NULL,
                is_hymn_slot INTEGER DEFAULT 0,
                FOREIGN KEY (template_id) REFERENCES service_templates(id) ON DELETE CASCADE
            );
        """)
        # Deduplicate hymns where REPLACE(LOWER(file_path), '/', '\') matches
        # 1. Update service_items references from old duplicate hymn_id to MAX(id)
        cursor.execute("""
            UPDATE service_items
            SET hymn_id = (
                SELECT MAX(h2.id)
                FROM hymns h1
                JOIN hymns h2 ON REPLACE(LOWER(h1.file_path), '/', '\\') = REPLACE(LOWER(h2.file_path), '/', '\\')
                WHERE h1.id = service_items.hymn_id
            )
            WHERE hymn_id IS NOT NULL AND hymn_id IN (
                SELECT h1.id FROM hymns h1
                JOIN hymns h2 ON REPLACE(LOWER(h1.file_path), '/', '\\') = REPLACE(LOWER(h2.file_path), '/', '\\') AND h1.id < h2.id
            );
        """)
        
        # 2. Delete duplicate hymns keeping MAX(id)
        cursor.execute("""
            DELETE FROM hymns
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM hymns
                GROUP BY REPLACE(LOWER(file_path), '/', '\\')
            );
        """)

        # 3. Normalize surviving file_path values to standard format
        cursor.execute("SELECT id, file_path FROM hymns")
        for r in cursor.fetchall():
            norm = normalize_path(r['file_path'])
            if norm != r['file_path']:
                cursor.execute("UPDATE hymns SET file_path = ? WHERE id = ?", (norm, r['id']))
        conn.commit()

def save_hymns(hymns_list, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        for h in hymns_list:
            norm_path = normalize_path(h.get('file_path'))
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
                norm_path,
                h.get('liturgical_season', 'General')
            ))
        conn.commit()


def search_hymns(query=None, season=None, category_type=None, disc=None, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM hymns WHERE 1=1"
        params = []
        order_by_case = ""
        order_params = []
        
        if category_type == 'hymn':
            sql += " AND hymn_number IS NOT NULL"
        elif category_type == 'liturgy':
            sql += " AND hymn_number IS NULL"

        if query:
            query_str = str(query).strip()
            q_lower = query_str.lower()
            if query_str.isdigit():
                sql += " AND (hymn_number = ? OR title LIKE ? OR liturgical_season LIKE ?)"
                params.extend([int(query_str), f"%{query_str}%", f"%{query_str}%"])
                order_by_case = "CASE WHEN hymn_number = ? THEN 0 WHEN LOWER(title) = LOWER(?) THEN 1 WHEN LOWER(title) LIKE LOWER(?) || '%' THEN 2 ELSE 3 END ASC, "
                order_params = [int(query_str), query_str, query_str]
            elif q_lower in ('matins', 'ma'):
                sql += " AND (liturgical_season = 'Matins' OR title LIKE 'MA - %' OR title LIKE '%matins%')"
            elif q_lower in ('vespers', 've'):
                sql += " AND (liturgical_season = 'Vespers' OR title LIKE 'VE - %' OR title LIKE '%vespers%')"
            elif q_lower in ('compline', 'co'):
                sql += " AND (liturgical_season = 'Compline' OR title LIKE 'CO - %' OR title LIKE '%compline%')"
            elif q_lower in ('morning prayer', 'mp'):
                sql += " AND (liturgical_season = 'Morning Prayer' OR title LIKE 'MP - %' OR title LIKE '%morning prayer%')"
            elif q_lower in ('evening prayer', 'ep'):
                sql += " AND (liturgical_season = 'Evening Prayer' OR title LIKE 'EP - %' OR title LIKE '%evening prayer%')"
            else:
                sql += " AND (title LIKE ? OR liturgical_season LIKE ?)"
                params.extend([f"%{query_str}%", f"%{query_str}%"])
                order_by_case = "CASE WHEN LOWER(title) = LOWER(?) THEN 0 WHEN LOWER(title) LIKE LOWER(?) || '%' THEN 1 ELSE 2 END ASC, "
                order_params = [query_str, query_str]

        if season:
            sql += " AND liturgical_season = ?"
            params.append(season)
            
        if disc:
            sql += " AND disc_number = ?"
            params.append(int(disc))
            
        sql += f" ORDER BY {order_by_case}disc_number ASC, track_number ASC"
        params.extend(order_params)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_hymn_by_id(hymn_id, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hymns WHERE id = ?", (hymn_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
