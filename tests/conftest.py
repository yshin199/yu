import pytest
from app import db as dbmod


@pytest.fixture
def db(tmp_path):
    conn = dbmod.connect(tmp_path / "test.db")
    dbmod.init_schema(conn)
    yield conn
    conn.close()
