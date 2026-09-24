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
