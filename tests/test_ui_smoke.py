from app import classifier
from app.ui.app import App
from app.ui.home import HomeView


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
