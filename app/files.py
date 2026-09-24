import os
from datetime import datetime
from pathlib import Path

from .models import FileEntry


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _to(row):
    if row is None:
        return None
    return FileEntry(**dict(row))


def infer_type(file_name):
    return Path(file_name).suffix.lower().lstrip(".")


def add_file(conn, file_name, original_path, size=0, category_id=None):
    p = str(original_path)
    if size == 0 and os.path.exists(p):
        size = os.path.getsize(p)
    cur = conn.execute(
        "INSERT INTO files (file_name, original_path, file_type, category_id, size, created_at, status) "
        "VALUES (?,?,?,?,?,?,?)",
        (file_name, p, infer_type(file_name), category_id, size, _now(), "indexed"))
    conn.commit()
    return get_file(conn, cur.lastrowid)


def get_file(conn, file_id):
    return _to(conn.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone())


def set_file_category(conn, file_id, category_id):
    conn.execute("UPDATE files SET category_id=? WHERE id=?", (category_id, file_id))
    conn.commit()


def set_file_note(conn, file_id, note):
    conn.execute("UPDATE files SET note=? WHERE id=?", (note, file_id))
    conn.commit()


def delete_file_entry(conn, file_id):
    conn.execute("DELETE FROM files WHERE id=?", (file_id,))
    conn.commit()


def list_files(conn, category_id=None, query=None, file_type=None, include_descendants=False):
    sql = "SELECT * FROM files WHERE 1=1"
    params = []
    if category_id is not None:
        if include_descendants:
            from .categories import get_descendant_ids
            ids = get_descendant_ids(conn, category_id)
            sql += f" AND category_id IN ({','.join('?' * len(ids))})"
            params += ids
        else:
            sql += " AND category_id=?"
            params.append(category_id)
    if query:
        sql += " AND file_name LIKE ?"
        params.append(f"%{query}%")
    if file_type:
        sql += " AND file_type=?"
        params.append(file_type)
    sql += " ORDER BY created_at DESC, id DESC"
    return [_to(r) for r in conn.execute(sql, params).fetchall()]
