from typing import Optional

from .models import Category


def _to(row):
    if row is None:
        return None
    return Category(**dict(row))


def add_category(conn, name, parent_id=None, sort_order=0):
    cur = conn.execute(
        "INSERT INTO categories (name, parent_id, sort_order) VALUES (?,?,?)",
        (name, parent_id, sort_order))
    conn.commit()
    return get_category(conn, cur.lastrowid)


def get_category(conn, category_id):
    row = conn.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()
    return _to(row)


def list_categories(conn):
    rows = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    return [_to(r) for r in rows]


def list_children(conn, parent_id=None):
    if parent_id is None:
        rows = conn.execute(
            "SELECT * FROM categories WHERE parent_id IS NULL ORDER BY sort_order, id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories WHERE parent_id=? ORDER BY sort_order, id",
            (parent_id,)).fetchall()
    return [_to(r) for r in rows]


def rename_category(conn, category_id, name):
    conn.execute("UPDATE categories SET name=? WHERE id=?", (name, category_id))
    conn.commit()


def get_descendant_ids(conn, category_id):
    seen, frontier = [], [category_id]
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.append(cur)
        for row in conn.execute(
                "SELECT id FROM categories WHERE parent_id=?", (cur,)).fetchall():
            frontier.append(row["id"])
    return seen


def delete_category(conn, category_id):
    ids = get_descendant_ids(conn, category_id)
    ph = ",".join("?" * len(ids))
    conn.execute(f"UPDATE files SET category_id=NULL WHERE category_id IN ({ph})", ids)
    conn.execute(f"UPDATE memos SET category_id=NULL WHERE category_id IN ({ph})", ids)
    conn.execute(f"DELETE FROM categories WHERE id IN ({ph})", ids)
    conn.commit()


def category_path(conn, category_id):
    names = []
    cur = category_id
    while cur is not None:
        row = conn.execute("SELECT * FROM categories WHERE id=?", (cur,)).fetchone()
        if row is None:
            break
        names.append(row["name"])
        cur = row["parent_id"]
    return list(reversed(names))


def build_tree(conn):
    cats = list_categories(conn)
    by_parent = {}
    for c in cats:
        by_parent.setdefault(c.parent_id, []).append(c)

    def node(c):
        return {"id": c.id, "name": c.name,
                "children": [node(k) for k in by_parent.get(c.id, [])]}

    return [node(c) for c in by_parent.get(None, [])]
