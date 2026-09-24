from app.memos import (add_memo, get_memo, set_memo_done, set_memo_pinned,
                       set_memo_archived, delete_memo, list_memos, get_today_plans)


def test_add_memo_defaults(db):
    m = add_memo(db, title="标题", content="内容")
    assert m.memo_type == "note"
    assert m.done is False and m.archived is False and m.pinned is False


def test_today_plans(db):
    add_memo(db, title="买菜", memo_type="plan", plan_date="2026-09-24")
    add_memo(db, title="旧计划", memo_type="plan", plan_date="2026-09-23")
    add_memo(db, title="普通", memo_type="note")
    plans = get_today_plans(db, "2026-09-24")
    assert [p.title for p in plans] == ["买菜"]


def test_done_and_archive(db):
    m = add_memo(db, title="a", memo_type="plan", plan_date="2026-09-24")
    set_memo_done(db, m.id, True)
    assert get_memo(db, m.id).done is True
    set_memo_archived(db, m.id, True)
    assert get_memo(db, m.id).archived is True


def test_pinned(db):
    m = add_memo(db, title="a")
    set_memo_pinned(db, m.id, True)
    assert get_memo(db, m.id).pinned is True


def test_list_filters(db):
    add_memo(db, title="买牛奶", content="超市")
    add_memo(db, title="写报告")
    assert len(list_memos(db, query="牛奶")) == 1
    assert len(list_memos(db, memo_type="note")) == 2


def test_delete(db):
    m = add_memo(db, title="a")
    delete_memo(db, m.id)
    assert get_memo(db, m.id) is None
