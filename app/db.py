import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / "文档管理数据" / "app.db"
DEFAULT_ORGANIZE_DIR = Path.home() / "文档管理数据" / "文件库"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  parent_id INTEGER,
  sort_order INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT NOT NULL,
  original_path TEXT NOT NULL,
  file_type TEXT DEFAULT '',
  category_id INTEGER,
  note TEXT DEFAULT '',
  size INTEGER DEFAULT 0,
  created_at TEXT DEFAULT '',
  status TEXT DEFAULT 'indexed'
);
CREATE TABLE IF NOT EXISTS memos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT DEFAULT '',
  content TEXT DEFAULT '',
  memo_type TEXT DEFAULT 'note',
  category_id INTEGER,
  pinned INTEGER DEFAULT 0,
  done INTEGER DEFAULT 0,
  archived INTEGER DEFAULT 0,
  plan_date TEXT,
  created_at TEXT DEFAULT '',
  updated_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  match_value TEXT NOT NULL,
  target_category_id INTEGER NOT NULL,
  enabled INTEGER DEFAULT 1
);
"""


def connect(db_path=DEFAULT_DB_PATH):
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn):
    conn.executescript(_SCHEMA)
    conn.commit()
