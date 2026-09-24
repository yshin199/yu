from .models import FileEntry, Memo


def _files(rows):
    return [FileEntry(**dict(r)) for r in rows]


def _memos(rows):
    return [Memo(**{k: (bool(v) if k in ("pinned", "done", "archived") else v)
                    for k, v in dict(r).items()}) for r in rows]


def home_summary(conn, today_iso=None, recent_limit=5):
    file_total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    file_unc = conn.execute(
        "SELECT COUNT(*) FROM files WHERE category_id IS NULL").fetchone()[0]
    recent_files = _files(conn.execute(
        "SELECT * FROM files ORDER BY created_at DESC, id DESC LIMIT ?",
        (recent_limit,)).fetchall())
    memo_total = conn.execute(
        "SELECT COUNT(*) FROM memos WHERE archived=0").fetchone()[0]
    plan_incomplete = 0
    if today_iso is not None:
        plan_incomplete = conn.execute(
            "SELECT COUNT(*) FROM memos WHERE memo_type='plan' AND plan_date=? "
            "AND archived=0 AND done=0", (today_iso,)).fetchone()[0]
    recent_memos = _memos(conn.execute(
        "SELECT * FROM memos WHERE archived=0 ORDER BY created_at DESC, id DESC LIMIT ?",
        (recent_limit,)).fetchall())
    return {
        "file_total": file_total,
        "file_uncategorized": file_unc,
        "recent_files": recent_files,
        "plan_incomplete": plan_incomplete,
        "memo_total": memo_total,
        "recent_memos": recent_memos,
    }
