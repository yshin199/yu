from app.stats import home_summary
from app.files import add_file
from app.memos import add_memo


def test_home_summary_counts(db):
    add_file(db, "a.pdf", "/a.pdf")
    add_file(db, "b.jpg", "/b.jpg")
    add_memo(db, title="买菜", memo_type="plan", plan_date="2026-09-24")
    add_memo(db, title="记", memo_type="note")
    s = home_summary(db, today_iso="2026-09-24")
    assert s["file_total"] == 2
    assert s["file_uncategorized"] == 2
    assert s["plan_incomplete"] == 1
    assert s["memo_total"] == 2
    assert len(s["recent_files"]) == 2
    assert len(s["recent_memos"]) == 2


def test_home_summary_empty_db(db):
    s = home_summary(db, today_iso="2026-09-24")
    assert s["file_total"] == 0
    assert s["file_uncategorized"] == 0
    assert s["plan_incomplete"] == 0
    assert s["memo_total"] == 0
    assert s["recent_files"] == []
    assert s["recent_memos"] == []
