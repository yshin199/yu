import shutil
from pathlib import Path

from .categories import category_path


def _unique_dest(dest_dir, name):
    p = Path(dest_dir) / name
    if not p.exists():
        return p
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 1
    while True:
        cand = Path(dest_dir) / f"{stem} ({i}){suffix}"
        if not cand.exists():
            return cand
        i += 1


def organize_category(conn, category_id, root_dir):
    names = category_path(conn, category_id)
    dest_dir = Path(root_dir)
    for n in names:
        dest_dir = dest_dir / n
    dest_dir.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        "SELECT * FROM files WHERE category_id=? AND status='indexed' ORDER BY id",
        (category_id,)).fetchall()
    moved = 0
    skipped_missing = 0
    for row in rows:
        src = Path(row["original_path"])
        if not src.exists():
            skipped_missing += 1
            continue
        dest = _unique_dest(dest_dir, row["file_name"])
        shutil.move(str(src), str(dest))
        conn.execute(
            "UPDATE files SET original_path=?, status='organized' WHERE id=?",
            (str(dest), row["id"]))
        moved += 1
    conn.commit()
    return {"moved": moved, "skipped_missing": skipped_missing, "skipped_collision": 0}
