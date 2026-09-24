from datetime import datetime

from .models import Memo


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _to(row):
    if row is None:
        return None
    d = dict(row)
    return Memo(**{k: (bool(v) if k in ("pinned", "done", "archived") else v)
                   for k, v in d.items()})


def add_memo(conn, title="", content="", memo_type="note", category_id=None, plan_date=None):
    ts = _now()
    cur = conn.execute(
        "INSERT INTO memos (title, content, memo_type, category_id, plan_date, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (title, content, memo_type, category_id, plan_date, ts, ts))
    conn.commit()
    return get_memo(conn, cur.lastrowid)


def get_memo(conn, memo_id):
    return _to(conn.execute("SELECT * FROM memos WHERE id=?", (memo_id,)).fetchone())


def update_memo(conn, memo_id, title=None, content=None, category_id=None, plan_date=None):
    sets, params = [], []
    if title is not None:
        sets.append("title=?"); params.append(title)
    if content is not None:
        sets.append("content=?"); params.append(content)
    if category_id is not None:
        sets.append("category_id=?"); params.append(category_id)
    if plan_date is not None:
        sets.append("plan_date=?"); params.append(plan_date)
    if sets:
        sets.append("updated_at=?"); params.append(_now())
        params.append(memo_id)
        conn.execute(f"UPDATE memos SET {', '.join(sets)} WHERE id=?", params)
        conn.commit()


def set_memo_done(conn, memo_id, done):
    conn.execute("UPDATE memos SET done=?, updated_at=? WHERE id=?",
                 (1 if done else 0, _now(), memo_id))
    conn.commit()


def set_memo_pinned(conn, memo_id, pinned):
    conn.execute("UPDATE memos SET pinned=?, updated_at=? WHERE id=?",
                 (1 if pinned else 0, _now(), memo_id))
    conn.commit()


def set_memo_archived(conn, memo_id, archived):
    conn.execute("UPDATE memos SET archived=?, updated_at=? WHERE id=?",
                 (1 if archived else 0, _now(), memo_id))
    conn.commit()


def delete_memo(conn, memo_id):
    conn.execute("DELETE FROM memos WHERE id=?", (memo_id,))
    conn.commit()


def list_memos(conn, query=None, memo_type=None, archived=None, category_id=None):
    sql = "SELECT * FROM memos WHERE 1=1"
    params = []
    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params += [f"%{query}%", f"%{query}%"]
    if memo_type:
        sql += " AND memo_type=?"; params.append(memo_type)
    if archived is not None:
        sql += " AND archived=?"; params.append(1 if archived else 0)
    if category_id is not None:
        sql += " AND category_id=?"; params.append(category_id)
    sql += " ORDER BY pinned DESC, created_at DESC, id DESC"
    return [_to(r) for r in conn.execute(sql, params).fetchall()]


def get_today_plans(conn, date_iso):
    rows = conn.execute(
        "SELECT * FROM memos WHERE memo_type='plan' AND plan_date=? AND archived=0 "
        "ORDER BY done ASC, created_at ASC, id ASC", (date_iso,)).fetchall()
    return [_to(r) for r in rows]
