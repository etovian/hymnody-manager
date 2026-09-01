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
            query_str = str(query).strip()
            if query_str.isdigit():
                sql += " AND (hymn_number = ? OR title LIKE ? OR liturgical_season LIKE ?)"
                params.extend([int(query_str), f"%{query_str}%", f"%{query_str}%"])
            else:
                sql += " AND (title LIKE ? OR liturgical_season LIKE ?)"
                params.extend([f"%{query_str}%", f"%{query_str}%"])
                
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
