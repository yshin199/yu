import sqlite3
from pathlib import Path


def export_backup(conn, dest_path):
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    target = sqlite3.connect(str(dest))
    try:
        conn.backup(target)
    finally:
        target.close()
    return str(dest)


def restore_backup(conn, source_path):
    src = sqlite3.connect(str(source_path))
    try:
        src.backup(conn)
    finally:
        src.close()
    conn.commit()
