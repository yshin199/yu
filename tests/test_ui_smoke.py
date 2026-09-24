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


def test_select_range(root, db):
    from app import files
    files.add_file(db, "a.txt", "/a.txt")
    files.add_file(db, "b.txt", "/b.txt")
    files.add_file(db, "c.txt", "/c.txt")
    view = DocumentsView(root, db)
    view.refresh()
    children = view.tree.get_children()
    # 拖到最后一个 → 全选
    view._select_range(children[0], children[2])
    assert set(view.tree.selection()) == set(children)
    # 拖到第二个 → 只选前两个
    view._select_range(children[0], children[1])
    assert set(view.tree.selection()) == {children[0], children[1]}
    # 反向拖动等价
    view._select_range(children[2], children[0])
    assert set(view.tree.selection()) == set(children)
