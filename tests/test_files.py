from app.files import (infer_type, add_file, get_file, set_file_category,
                       set_file_note, delete_file_entry, list_files)


def test_infer_type():
    assert infer_type("a.pdf") == "pdf"
    assert infer_type("B.JPG") == "jpg"
    assert infer_type("archive.tar.gz") == "gz"
    assert infer_type("README") == ""          # Review Focus #1


def test_add_and_get(db):
    f = add_file(db, "报告.pdf", "/docs/报告.pdf", size=100)
    assert f.file_type == "pdf"
    assert f.status == "indexed"
    assert f.category_id is None
    assert get_file(db, f.id).file_name == "报告.pdf"


def test_set_category_and_note(db):
    f = add_file(db, "a.txt", "/a.txt")
    set_file_category(db, f.id, 9)
    set_file_note(db, f.id, "说明")
    g = get_file(db, f.id)
    assert g.category_id == 9 and g.note == "说明"


def test_list_files_filters(db):
    a = add_file(db, "a.pdf", "/a.pdf")
    add_file(db, "b.jpg", "/b.jpg")
    db.execute("INSERT INTO categories (name) VALUES ('文档')")
    db.commit()
    set_file_category(db, a.id, 1)
    # 按分类过滤
    assert [f.id for f in list_files(db, category_id=1)] == [a.id]
    # 按类型过滤
    assert len(list_files(db, file_type="jpg")) == 1
    # 按文件名搜索
    assert len(list_files(db, query="b")) == 1


def test_delete_entry_keeps_file(db):
    f = add_file(db, "a.txt", "/a.txt")
    delete_file_entry(db, f.id)
    assert get_file(db, f.id) is None


def test_add_file_stats_size(db, tmp_path):
    p = tmp_path / "data.txt"
    p.write_bytes(b"hello world")  # 11 bytes
    f = add_file(db, "data.txt", p)
    assert f.size == 11
