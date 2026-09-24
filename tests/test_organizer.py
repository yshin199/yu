from app.organizer import organize_category
from app.categories import add_category
from app.files import add_file, get_file


def _touch(p, text=b""):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text)


def test_moves_files(db, tmp_path):
    src1 = tmp_path / "src" / "a.pdf"; _touch(src1, b"1")
    src2 = tmp_path / "src" / "b.pdf"; _touch(src2, b"2")
    cat = add_category(db, "文档")
    add_file(db, "a.pdf", src1, category_id=cat.id)
    add_file(db, "b.pdf", src2, category_id=cat.id)
    root = tmp_path / "out"
    res = organize_category(db, cat.id, root)
    assert res["moved"] == 2
    assert (root / "文档" / "a.pdf").exists()
    assert (root / "文档" / "b.pdf").exists()
    assert not src1.exists()


def test_missing_source_skipped(db, tmp_path):
    cat = add_category(db, "文档")
    f = add_file(db, "gone.pdf", tmp_path / "no" / "gone.pdf", category_id=cat.id)
    res = organize_category(db, cat.id, tmp_path / "out")
    assert res["moved"] == 0 and res["skipped_missing"] == 1      # Review Focus #2
    assert get_file(db, f.id).status == "indexed"


def test_collision_gets_suffix(db, tmp_path):
    src = tmp_path / "s" / "a.pdf"; _touch(src, b"x")
    cat = add_category(db, "文档")
    add_file(db, "a.pdf", src, category_id=cat.id)
    root = tmp_path / "out"
    (root / "文档").mkdir(parents=True)
    (root / "文档" / "a.pdf").write_bytes(b"existing")
    res = organize_category(db, cat.id, root)
    assert res["moved"] == 1
    assert (root / "文档" / "a (1).pdf").exists()                 # Review Focus #3
    assert (root / "文档" / "a.pdf").read_bytes() == b"existing"  # 不覆盖
