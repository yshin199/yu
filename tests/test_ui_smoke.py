from app import classifier
from app.ui.app import App
from app.ui.documents import DocumentsView
from app.ui.home import HomeView
from app.ui.memos_view import MemosView


def test_app_builds(root, db):
    classifier.seed_defaults(db)
    app = App(root, db)
    app.show_home()
    root.update()
    assert app.winfo_exists()


def test_home_view_builds(root, db):
    classifier.seed_defaults(db)
    view = HomeView(root, db)
    view.refresh()
    root.update()
    assert view.winfo_exists()


def test_documents_view_builds(root, db):
    classifier.seed_defaults(db)
    view = DocumentsView(root, db)
    view.refresh()
    root.update()
    assert view.winfo_exists()


def test_memos_view_builds(root, db):
    classifier.seed_defaults(db)
    view = MemosView(root, db)
    view.refresh()
    root.update()
    assert view.winfo_exists()


def test_documents_view_filters_by_category(root, db):
    from app import categories, files
    cat = categories.add_category(db, "工作")
    f1 = files.add_file(db, "a.pdf", "/a.pdf", category_id=cat.id)
    files.add_file(db, "b.pdf", "/b.pdf")
    view = DocumentsView(root, db)
    view.set_category(cat.id)
    view.refresh()
    root.update()
    assert [int(i) for i in view.tree.get_children()] == [f1.id]


def test_memos_view_filters_by_category(root, db):
    from app import categories, memos
    cat = categories.add_category(db, "工作")
    m1 = memos.add_memo(db, title="工作备忘", category_id=cat.id)
    memos.add_memo(db, title="普通备忘")
    view = MemosView(root, db)
    view.set_category(cat.id)
    view.refresh()
    root.update()
    assert [int(i) for i in view.tree.get_children()] == [m1.id]


def test_register_paths_into_selected_category(root, db, tmp_path):
    from app import categories, files
    cat = categories.add_category(db, "工作")
    view = DocumentsView(root, db)
    view.set_category(cat.id)
    p = tmp_path / "a.txt"
    p.write_bytes(b"x")
    view._register_paths([str(p)])
    root.update()
    ids = [int(i) for i in view.tree.get_children()]
    assert len(ids) == 1
    assert files.get_file(db, ids[0]).category_id == cat.id


def test_assign_ids_multiple(root, db):
    from app import categories, files
    cat = categories.add_category(db, "工作")
    f1 = files.add_file(db, "a.txt", "/a.txt")
    f2 = files.add_file(db, "b.txt", "/b.txt")
    view = DocumentsView(root, db)
    view._assign_ids([f1.id, f2.id], cat.id)
    assert files.get_file(db, f1.id).category_id == cat.id
    assert files.get_file(db, f2.id).category_id == cat.id


def test_delete_ids_multiple(root, db):
    from app import files
    f1 = files.add_file(db, "a.txt", "/a.txt")
    f2 = files.add_file(db, "b.txt", "/b.txt")
    view = DocumentsView(root, db)
    view._delete_ids([f1.id, f2.id])
    assert files.get_file(db, f1.id) is None
    assert files.get_file(db, f2.id) is None


def test_auto_classify_ids(root, db):
    from app import classifier, files
    classifier.seed_defaults(db)
    f = files.add_file(db, "报告.pdf", "/报告.pdf")
    view = DocumentsView(root, db)
    assigned, unmatched = view._auto_classify_ids([f.id])
    assert assigned == 1 and unmatched == 0
    assert files.get_file(db, f.id).category_id is not None


def test_rect_intersects():
    from app.ui.documents import _rect_intersects
    # bbox (x=0, y=0, w=100, h=20)
    assert _rect_intersects(0, 0, 100, 20, -10, -10, 10000, 10000) is True
    assert _rect_intersects(0, 0, 100, 20, 200, 200, 300, 300) is False
    # 部分重叠
    assert _rect_intersects(0, 0, 100, 20, 50, -5, 150, 5) is True
    # 矩形反向（从右下往左上拖）
    assert _rect_intersects(0, 0, 100, 20, 10000, 10000, -10, -10) is True
