import pytest
from app import db


@pytest.fixture
def db(tmp_path):
    conn = db.connect(tmp_path / "test.db")
    db.init_schema(conn)
    yield conn
    conn.close()
