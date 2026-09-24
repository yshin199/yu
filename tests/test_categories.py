from app.categories import (
    add_category, get_category, list_children, rename_category,
    delete_category, get_descendant_ids, category_path, build_tree,
)


def test_add_and_get(db):
    c = add_category(db, "工作")
    assert c.id is not None
    assert get_category(db, c.id).name == "工作"


def test_hierarchy(db):
    work = add_category(db, "工作")
    contract = add_category(db, "合同", parent_id=work.id)
    kids = list_children(db, work.id)
    assert [k.name for k in kids] == ["合同"]
    assert contract.parent_id == work.id


def test_rename(db):
    c = add_category(db, "旧名")
    rename_category(db, c.id, "新名")
    assert get_category(db, c.id).name == "新名"


def test_descendants(db):
    a = add_category(db, "a")
    b = add_category(db, "b", a.id)
    c = add_category(db, "c", b.id)
    ids = set(get_descendant_ids(db, a.id))
    assert ids == {a.id, b.id, c.id}


def test_delete_reassigns_items(db):
    work = add_category(db, "工作")
    db.execute("INSERT INTO files (file_name, original_path, category_id) VALUES (?,?,?)",
               ("a.pdf", "/a.pdf", work.id))
    db.execute("INSERT INTO memos (title, content, category_id) VALUES (?,?,?)",
               ("m", "x", work.id))
    db.commit()
    delete_category(db, work.id)
    assert get_category(db, work.id) is None
    assert db.execute("SELECT category_id FROM files").fetchone()[0] is None
    assert db.execute("SELECT category_id FROM memos").fetchone()[0] is None


def test_delete_cascades_children(db):
    a = add_category(db, "a")
    add_category(db, "b", a.id)
    delete_category(db, a.id)
    assert list_children(db, a.id) == []


def test_category_path(db):
    a = add_category(db, "工作")
    b = add_category(db, "合同", a.id)
    assert category_path(db, b.id) == ["工作", "合同"]


def test_build_tree(db):
    a = add_category(db, "工作")
    add_category(db, "合同", a.id)
    tree = build_tree(db)
    assert tree[0]["name"] == "工作"
    assert tree[0]["children"][0]["name"] == "合同"


def test_delete_category_removes_rules(db):
    work = add_category(db, "工作")
    db.execute("INSERT INTO rules (kind, match_value, target_category_id) VALUES (?,?,?)",
               ("keyword", "合同", work.id))
    db.commit()
    delete_category(db, work.id)
    assert db.execute("SELECT COUNT(*) FROM rules").fetchone()[0] == 0
