from app import db


def test_connect_creates_parent(tmp_path):
    p = tmp_path / "sub" / "app.db"
    conn = db.connect(p)
    conn.close()
    assert p.exists()


def test_init_schema_creates_tables(tmp_path):
    conn = db.connect(tmp_path / "a.db")
    db.init_schema(conn)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"categories", "files", "memos", "rules"} <= names


def test_init_schema_is_idempotent(tmp_path):
    conn = db.connect(tmp_path / "b.db")
    db.init_schema(conn)
    db.init_schema(conn)  # 不抛异常
    conn.close()
