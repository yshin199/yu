from app.models import Category, FileEntry, Memo, Rule


def test_category_defaults():
    c = Category(id=1, name="工作")
    assert c.parent_id is None
    assert c.sort_order == 0


def test_file_entry_defaults():
    f = FileEntry(id=1, file_name="a.pdf", original_path="/x/a.pdf")
    assert f.file_type == ""          # 由 files.infer_type 单独推断，模型不管
    assert f.category_id is None
    assert f.status == "indexed"


def test_memo_defaults():
    m = Memo(id=1, title="t", content="c")
    assert m.memo_type == "note"
    assert m.pinned is False and m.done is False and m.archived is False


def test_rule_fields():
    r = Rule(id=1, kind="type", match_value="pdf", target_category_id=2)
    assert r.enabled is True
