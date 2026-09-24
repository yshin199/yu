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
