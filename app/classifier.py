from .models import FileEntry, Rule
from .categories import add_category, list_categories
from .files import get_file

DEFAULT_CATEGORIES = ["文档", "图片", "表格", "视频", "音频", "压缩包", "程序"]
DEFAULT_TYPE_RULES = {
    "pdf": "文档", "doc": "文档", "docx": "文档", "txt": "文档", "md": "文档",
    "jpg": "图片", "jpeg": "图片", "png": "图片", "gif": "图片", "bmp": "图片", "svg": "图片",
    "xls": "表格", "xlsx": "表格", "csv": "表格",
    "mp4": "视频", "mov": "视频", "avi": "视频", "mkv": "视频",
    "mp3": "音频", "wav": "音频",
    "zip": "压缩包", "rar": "压缩包", "7z": "压缩包",
    "exe": "程序", "msi": "程序",
}


def seed_defaults(conn):
    existing = {c.name: c.id for c in list_categories(conn)}
    name_to_id = {}
    for name in DEFAULT_CATEGORIES:
        if name in existing:
            name_to_id[name] = existing[name]
        else:
            cat = add_category(conn, name)
            name_to_id[name] = cat.id
            existing[name] = cat.id
    have = {(r["kind"], r["match_value"]) for r in conn.execute(
        "SELECT kind, match_value FROM rules WHERE kind='type'")}
    for ext, cat_name in DEFAULT_TYPE_RULES.items():
        if ("type", ext) not in have:
            conn.execute(
                "INSERT INTO rules (kind, match_value, target_category_id, enabled) VALUES (?,?,?,1)",
                ("type", ext, name_to_id[cat_name]))
    conn.commit()


def add_rule(conn, kind, match_value, target_category_id):
    cur = conn.execute(
        "INSERT INTO rules (kind, match_value, target_category_id, enabled) VALUES (?,?,?,1)",
        (kind, match_value, target_category_id))
    conn.commit()
    row = conn.execute("SELECT * FROM rules WHERE id=?", (cur.lastrowid,)).fetchone()
    d = dict(row)
    return Rule(**{**d, "enabled": bool(d["enabled"])})


def list_rules(conn):
    rows = conn.execute("SELECT * FROM rules ORDER BY id").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        out.append(Rule(**{**d, "enabled": bool(d["enabled"])}))
    return out


def delete_rule(conn, rule_id):
    conn.execute("DELETE FROM rules WHERE id=?", (rule_id,))
    conn.commit()


def _matching_rule(conn, file_entry):
    rules = list_rules(conn)
    keywords = [r for r in rules if r.enabled and r.kind == "keyword"]
    types = [r for r in rules if r.enabled and r.kind == "type"]
    for r in keywords:                       # 关键词优先
        if r.match_value and r.match_value in file_entry.file_name:
            return r
    for r in types:
        if file_entry.file_type and r.match_value.lower() == file_entry.file_type.lower():
            return r
    return None


def suggest_category(conn, file_id):
    f = get_file(conn, file_id)
    if f is None:
        return None
    r = _matching_rule(conn, f)
    return r.target_category_id if r else None


def preview_classification(conn):
    rows = conn.execute(
        "SELECT * FROM files WHERE category_id IS NULL ORDER BY id").fetchall()
    out = []
    for row in rows:
        f = FileEntry(**dict(row))
        r = _matching_rule(conn, f)
        out.append({
            "file_id": f.id,
            "file_name": f.file_name,
            "suggested_category_id": r.target_category_id if r else None,
        })
    return out
