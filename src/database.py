import sqlite3
import os
import re
from src.config import get_max_printed_hymn_number

DEFAULT_DB_PATH = "hymnody.db"


def is_in_printed_hymnal(hymn_number, max_num=None) -> bool:
    """Return True if hymn is in printed hymnal (or non-numbered liturgy), False if hymn_number > max_num."""
    if hymn_number is None:
        return True
    if max_num is None:
        max_num = get_max_printed_hymn_number()
    try:
        return int(hymn_number) <= max_num
    except (ValueError, TypeError):
        return True


def _annotate_hymn_dict(hymn_dict: dict, max_num=None) -> dict:
    if hymn_dict:
        hymn_dict["in_printed_hymnal"] = is_in_printed_hymnal(hymn_dict.get("hymn_number"), max_num=max_num)
    return hymn_dict


_WINDOWS_ABS = re.compile(r'^[A-Za-z]:[\\/]')


def normalize_path(path):
    """Canonicalize a file path for storage and deduplication.

    A path is normalized according to its own shape, not the host OS, so a
    hymnody.db written on a Windows node stays readable on macOS and vice
    versa: drive-lettered paths always canonicalize to Windows form
    (uppercase drive, backslashes), everything else to the native form.
    """
    if not path:
        return ""
    if _WINDOWS_ABS.match(path):
        norm = os.path.abspath(path) if os.name == 'nt' else path
        norm = norm.replace('/', '\\')
        return norm[0].upper() + norm[1:]
    norm = os.path.abspath(path)
    if _WINDOWS_ABS.match(norm):
        norm = norm.replace('/', '\\')
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
            CREATE TABLE IF NOT EXISTS sources (
                code TEXT PRIMARY KEY,
                meaning TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tunes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hymns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hymn_number INTEGER,
                title TEXT NOT NULL,
                disc_number INTEGER,
                track_number INTEGER,
                album TEXT,
                artist TEXT,
                year INTEGER,
                file_path TEXT UNIQUE,
                liturgical_season TEXT,
                tune_id INTEGER,
                source_code TEXT,
                lyrics TEXT,
                FOREIGN KEY (tune_id) REFERENCES tunes(id),
                FOREIGN KEY (source_code) REFERENCES sources(code)
            );
        """)

        # Migration check for existing DBs where hymns.file_path may be NOT NULL or missing tune_id/source_code
        cursor.execute("PRAGMA table_info(hymns)")
        hymn_cols_info = cursor.fetchall()
        hymn_col_names = [col['name'] for col in hymn_cols_info]
        file_path_info = next((col for col in hymn_cols_info if col['name'] == 'file_path'), None)
        
        if file_path_info and file_path_info['notnull'] == 1:
            cursor.execute("PRAGMA foreign_keys=OFF")
            cursor.execute("""
                CREATE TABLE hymns_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hymn_number INTEGER,
                    title TEXT NOT NULL,
                    disc_number INTEGER,
                    track_number INTEGER,
                    album TEXT,
                    artist TEXT,
                    year INTEGER,
                    file_path TEXT UNIQUE,
                    liturgical_season TEXT,
                    tune_id INTEGER,
                    source_code TEXT,
                    lyrics TEXT,
                    FOREIGN KEY (tune_id) REFERENCES tunes(id),
                    FOREIGN KEY (source_code) REFERENCES sources(code)
                );
            """)
            cursor.execute("""
                INSERT INTO hymns_new (id, hymn_number, title, disc_number, track_number, album, artist, year, file_path, liturgical_season)
                SELECT id, hymn_number, title, disc_number, track_number, album, artist, year, file_path, liturgical_season FROM hymns
            """)
            cursor.execute("DROP TABLE hymns")
            cursor.execute("ALTER TABLE hymns_new RENAME TO hymns")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA table_info(hymns)")
            hymn_cols_info = cursor.fetchall()
            hymn_col_names = [col['name'] for col in hymn_cols_info]

        if 'tune_id' not in hymn_col_names:
            cursor.execute("ALTER TABLE hymns ADD COLUMN tune_id INTEGER")
        if 'source_code' not in hymn_col_names:
            cursor.execute("ALTER TABLE hymns ADD COLUMN source_code TEXT")
        if 'lyrics' not in hymn_col_names:
            cursor.execute("ALTER TABLE hymns ADD COLUMN lyrics TEXT")

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
                is_hymn_slot INTEGER DEFAULT 0,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
                FOREIGN KEY (hymn_id) REFERENCES hymns(id)
            );
        """)
        
        cursor.execute("PRAGMA table_info(service_items)")
        si_cols = [col['name'] for col in cursor.fetchall()]
        if 'is_hymn_slot' not in si_cols:
            cursor.execute("ALTER TABLE service_items ADD COLUMN is_hymn_slot INTEGER DEFAULT 0")
            cursor.execute("UPDATE service_items SET is_hymn_slot = 1 WHERE slot_name LIKE '%Hymn%'")

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

        # Seed sources, tunes, and catalog placeholder rows from src.lsb_seed_data
        from src.lsb_seed_data import SOURCES, TUNES, HYMN_CATALOG

        for code, meaning in SOURCES.items():
            cursor.execute(
                "INSERT INTO sources (code, meaning) VALUES (?, ?) ON CONFLICT(code) DO UPDATE SET meaning = excluded.meaning",
                (code, meaning)
            )

        for tune_name in TUNES:
            cursor.execute(
                "INSERT INTO tunes (name) VALUES (?) ON CONFLICT(name) DO NOTHING",
                (tune_name,)
            )

        cursor.execute("SELECT id, name FROM tunes")
        tune_map = {row['name']: row['id'] for row in cursor.fetchall()}

        for hymn_num, entry in HYMN_CATALOG.items():
            t_name = entry.get('tune')
            t_id = tune_map.get(t_name)
            s_code = entry.get('source')
            title = entry.get('title')
            season = entry.get('section')
            
            cursor.execute("SELECT id FROM hymns WHERE hymn_number = ?", (hymn_num,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE hymns
                    SET tune_id = ?,
                        source_code = ?,
                        liturgical_season = ?
                    WHERE hymn_number = ?
                """, (t_id, s_code, season, hymn_num))
            else:
                cursor.execute("""
                    INSERT INTO hymns (hymn_number, title, liturgical_season, tune_id, source_code)
                    VALUES (?, ?, ?, ?, ?)
                """, (hymn_num, title, season, t_id, s_code))

        # Deduplicate hymns:
        # For explicit tracks (disc_number > 0 and track_number > 0), deduplicate by (disc_number, track_number),
        # preferring canonical (non-suffixed) file paths over ' 1.m4a' suffixed ones.
        # For unnumbered/other tracks, deduplicate by normalized file_path.
        
        # 1. Update service_items references to point to surviving canonical hymn_id
        cursor.execute("""
            UPDATE service_items
            SET hymn_id = COALESCE((
                SELECT target.id
                FROM hymns current_hymn
                JOIN hymns target ON (
                    (current_hymn.disc_number > 0 AND current_hymn.track_number > 0 AND current_hymn.disc_number = target.disc_number AND current_hymn.track_number = target.track_number)
                    OR (current_hymn.file_path IS NOT NULL AND target.file_path IS NOT NULL AND REPLACE(LOWER(current_hymn.file_path), '/', '\\') = REPLACE(LOWER(target.file_path), '/', '\\'))
                )
                WHERE current_hymn.id = service_items.hymn_id
                ORDER BY 
                    CASE WHEN target.file_path GLOB '* [0-9].m4a' OR target.file_path GLOB '* [0-9][0-9].m4a' THEN 1 ELSE 0 END ASC,
                    LENGTH(target.file_path) ASC,
                    target.id DESC
                LIMIT 1
            ), service_items.hymn_id)
            WHERE hymn_id IS NOT NULL;
        """)
        
        # 2. Delete duplicate hymns, keeping surviving canonical entry
        cursor.execute("""
            DELETE FROM hymns
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY disc_number, track_number
                               ORDER BY 
                                   CASE WHEN file_path GLOB '* [0-9].m4a' OR file_path GLOB '* [0-9][0-9].m4a' THEN 1 ELSE 0 END ASC,
                                   LENGTH(file_path) ASC,
                                   id DESC
                           ) as rn
                    FROM hymns
                    WHERE disc_number > 0 AND track_number > 0
                    UNION ALL
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY REPLACE(LOWER(file_path), '/', '\\')
                               ORDER BY id DESC
                           ) as rn
                    FROM hymns
                    WHERE (disc_number <= 0 OR track_number <= 0 OR disc_number IS NULL OR track_number IS NULL)
                      AND file_path IS NOT NULL
                ) WHERE rn = 1
            ) AND file_path IS NOT NULL;
        """)

        # 3. Repair any service_items referencing deleted/orphaned hymn_ids by re-linking via file_path
        cursor.execute("""
            UPDATE service_items
            SET hymn_id = (
                SELECT h.id FROM hymns h
                WHERE REPLACE(LOWER(h.file_path), '/', '\\') = REPLACE(LOWER(service_items.file_path), '/', '\\')
                LIMIT 1
            )
            WHERE service_items.file_path IS NOT NULL 
              AND service_items.file_path != '' 
              AND (service_items.hymn_id IS NULL OR service_items.hymn_id NOT IN (SELECT id FROM hymns));
        """)

        # 4. Normalize surviving file_path values to standard format
        cursor.execute("SELECT id, file_path FROM hymns WHERE file_path IS NOT NULL")
        for r in cursor.fetchall():
            norm = normalize_path(r['file_path'])
            if norm != r['file_path']:
                cursor.execute("UPDATE hymns SET file_path = ? WHERE id = ?", (norm, r['id']))
        conn.commit()

def save_hymns(hymns_list, db_path=DEFAULT_DB_PATH):
    from src.lsb_seed_data import HYMN_CATALOG
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM tunes")
        tune_map = {row['name']: row['id'] for row in cursor.fetchall()}

        for h in hymns_list:
            norm_path = normalize_path(h.get('file_path')) if h.get('file_path') else None
            disc_num = h.get('disc_number', 1)
            track_num = h.get('track_number', 1)
            h_num = h.get('hymn_number')
            
            tune_id = h.get('tune_id')
            source_code = h.get('source_code')

            # Determine target_id: preserve explicitly passed 'id' or existing catalog ID matching hymn_number
            target_id = h.get('id')
            existing_row = None
            if target_id:
                cursor.execute("SELECT id, title, tune_id, source_code, lyrics FROM hymns WHERE id = ?", (target_id,))
                existing_row = cursor.fetchone()
            elif h_num:
                cursor.execute("SELECT id, title, tune_id, source_code, lyrics FROM hymns WHERE hymn_number = ?", (h_num,))
                existing_row = cursor.fetchone()
                if existing_row:
                    target_id = existing_row['id']

            if existing_row:
                if tune_id is None:
                    tune_id = existing_row['tune_id']
                if source_code is None:
                    source_code = existing_row['source_code']

            lyrics = h.get('lyrics') or (existing_row['lyrics'] if existing_row and 'lyrics' in existing_row.keys() else None)

            if (tune_id is None or source_code is None) and h_num and h_num in HYMN_CATALOG:
                cat_entry = HYMN_CATALOG[h_num]
                if source_code is None:
                    source_code = cat_entry.get('source')
                if tune_id is None and cat_entry.get('tune'):
                    tune_id = tune_map.get(cat_entry.get('tune'))

            # Check if (disc_number, track_number) already exists under a canonical (non-suffixed) file_path
            if norm_path and disc_num is not None and track_num is not None and disc_num > 0 and track_num > 0:
                existing = cursor.execute(
                    "SELECT id, file_path FROM hymns WHERE disc_number = ? AND track_number = ?", 
                    (disc_num, track_num)
                ).fetchall()
                
                is_candidate_suffixed = bool(re.search(r' \d+\.m4a$', norm_path, re.IGNORECASE))
                
                if is_candidate_suffixed:
                    has_canonical_existing = any(
                        ex['file_path'] and not re.search(r' \d+\.m4a$', ex['file_path'], re.IGNORECASE)
                        for ex in existing
                    )
                    if has_canonical_existing:
                        continue
                else:
                    for ex in existing:
                        if ex['file_path'] and re.search(r' \d+\.m4a$', ex['file_path'], re.IGNORECASE):
                            cursor.execute("DELETE FROM hymns WHERE id = ?", (ex['id'],))

            # Check if norm_path is already assigned to a DIFFERENT row id
            if norm_path:
                if target_id:
                    cursor.execute("DELETE FROM hymns WHERE file_path = ? AND id != ?", (norm_path, target_id))
                else:
                    cursor.execute("DELETE FROM hymns WHERE file_path = ?", (norm_path,))

            catalog_title = h.get('title') or (existing_row['title'] if existing_row and existing_row['title'] else None) or (HYMN_CATALOG.get(h_num, {}).get('title') if h_num else None)

            cursor.execute("""
                INSERT OR REPLACE INTO hymns 
                (id, hymn_number, title, disc_number, track_number, album, artist, year, file_path, liturgical_season, tune_id, source_code, lyrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                target_id,
                h_num,
                catalog_title,
                disc_num,
                track_num,
                h.get('album', 'The Concordia Organist'),
                h.get('artist', 'Concordia Publishing House'),
                h.get('year', 2009),
                norm_path,
                h.get('liturgical_season', 'General'),
                tune_id,
                source_code,
                lyrics
            ))
        conn.commit()


def get_all_hymns(db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hymns.*, tunes.name AS tune_name, sources.meaning AS source_meaning
            FROM hymns
            LEFT JOIN tunes ON hymns.tune_id = tunes.id
            LEFT JOIN sources ON hymns.source_code = sources.code
            ORDER BY CASE WHEN hymns.hymn_number IS NOT NULL THEN 0 ELSE 1 END ASC, hymns.hymn_number ASC, hymns.disc_number ASC, hymns.track_number ASC
        """)
        rows = cursor.fetchall()
        max_num = get_max_printed_hymn_number()
        return [_annotate_hymn_dict(dict(r), max_num=max_num) for r in rows]


def search_hymns(query=None, season=None, category_type=None, disc=None, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        sql = """
            SELECT hymns.*, tunes.name AS tune_name, sources.meaning AS source_meaning
            FROM hymns
            LEFT JOIN tunes ON hymns.tune_id = tunes.id
            LEFT JOIN sources ON hymns.source_code = sources.code
            WHERE 1=1
        """
        params = []
        order_by_case = ""
        order_params = []
        
        if category_type == 'hymn':
            sql += " AND hymns.hymn_number IS NOT NULL"
        elif category_type == 'liturgy':
            sql += " AND hymns.hymn_number IS NULL"

        if query:
            query_str = str(query).strip()
            q_lower = query_str.lower()
            if query_str.isdigit():
                sql += " AND (hymns.hymn_number = ? OR hymns.title LIKE ? OR hymns.liturgical_season LIKE ? OR tunes.name LIKE ? OR sources.meaning LIKE ?)"
                params.extend([int(query_str), f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"])
                order_by_case = "CASE WHEN hymns.hymn_number = ? THEN 0 WHEN LOWER(hymns.title) = LOWER(?) THEN 1 WHEN LOWER(hymns.title) LIKE LOWER(?) || '%' THEN 2 ELSE 3 END ASC, "
                order_params = [int(query_str), query_str, query_str]
            elif q_lower in ('matins', 'ma'):
                sql += " AND (hymns.liturgical_season = 'Matins' OR hymns.title LIKE 'MA - %' OR hymns.title LIKE '%matins%')"
            elif q_lower in ('vespers', 've'):
                sql += " AND (hymns.liturgical_season = 'Vespers' OR hymns.title LIKE 'VE - %' OR hymns.title LIKE '%vespers%')"
            elif q_lower in ('compline', 'co'):
                sql += " AND (hymns.liturgical_season = 'Compline' OR hymns.title LIKE 'CO - %' OR hymns.title LIKE '%compline%')"
            elif q_lower in ('morning prayer', 'mp'):
                sql += " AND (hymns.liturgical_season = 'Morning Prayer' OR hymns.title LIKE 'MP - %' OR hymns.title LIKE '%morning prayer%')"
            elif q_lower in ('evening prayer', 'ep'):
                sql += " AND (hymns.liturgical_season = 'Evening Prayer' OR hymns.title LIKE 'EP - %' OR hymns.title LIKE '%evening prayer%')"
            else:
                sql += " AND (hymns.title LIKE ? OR hymns.liturgical_season LIKE ? OR tunes.name LIKE ? OR sources.meaning LIKE ?)"
                params.extend([f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"])
                order_by_case = "CASE WHEN LOWER(hymns.title) = LOWER(?) THEN 0 WHEN LOWER(hymns.title) LIKE LOWER(?) || '%' THEN 1 ELSE 2 END ASC, "
                order_params = [query_str, query_str]

        if season:
            sql += " AND hymns.liturgical_season = ?"
            params.append(season)
            
        if disc:
            sql += " AND hymns.disc_number = ?"
            params.append(int(disc))
            
        hymn_order = "CASE WHEN hymns.hymn_number IS NOT NULL THEN 0 ELSE 1 END ASC, hymns.hymn_number ASC, " if category_type == 'hymn' or not category_type else ""
        sql += f" ORDER BY {order_by_case}{hymn_order}hymns.disc_number ASC, hymns.track_number ASC"
        params.extend(order_params)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        max_num = get_max_printed_hymn_number()
        return [_annotate_hymn_dict(dict(r), max_num=max_num) for r in rows]


def get_hymn_by_id(hymn_id, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hymns.*, tunes.name AS tune_name, sources.meaning AS source_meaning
            FROM hymns
            LEFT JOIN tunes ON hymns.tune_id = tunes.id
            LEFT JOIN sources ON hymns.source_code = sources.code
            WHERE hymns.id = ?
        """, (hymn_id,))
        row = cursor.fetchone()
        return _annotate_hymn_dict(dict(row)) if row else None


def get_hymn_usage_history(hymn_id, db_path=DEFAULT_DB_PATH):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id AS service_id,
                   s.service_date,
                   s.title AS service_title,
                   s.liturgical_day,
                   s.setting_preset,
                   si.slot_name,
                   si.sequence_order
            FROM service_items si
            JOIN services s ON si.service_id = s.id
            WHERE si.hymn_id = ?
            ORDER BY s.service_date DESC, s.id DESC, si.sequence_order ASC
        """, (hymn_id,))
        return [dict(r) for r in cursor.fetchall()]


def get_hymns_sharing_tune(tune_id, exclude_hymn_id=None, db_path=DEFAULT_DB_PATH):
    if not tune_id:
        return []
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        sql = """
            SELECT h.id, h.hymn_number, h.title, h.liturgical_season,
                   h.disc_number, h.track_number, h.file_path,
                   t.name AS tune_name, s.meaning AS source_meaning
            FROM hymns h
            LEFT JOIN tunes t ON h.tune_id = t.id
            LEFT JOIN sources s ON h.source_code = s.code
            WHERE h.tune_id = ?
        """
        params = [tune_id]
        if exclude_hymn_id is not None:
            sql += " AND h.id != ?"
            params.append(exclude_hymn_id)
        sql += """
            ORDER BY CASE WHEN h.hymn_number IS NOT NULL THEN 0 ELSE 1 END ASC,
                     h.hymn_number ASC, h.title ASC
        """
        cursor.execute(sql, params)
        max_num = get_max_printed_hymn_number()
        return [_annotate_hymn_dict(dict(r), max_num=max_num) for r in cursor.fetchall()]


def update_hymn_lyrics(hymn_id: int, lyrics: str | None, db_path=DEFAULT_DB_PATH) -> bool:
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE hymns SET lyrics = ? WHERE id = ?", (lyrics, hymn_id))
        conn.commit()
        return cursor.rowcount > 0


