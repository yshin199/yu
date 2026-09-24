from app.classifier import (seed_defaults, add_rule, suggest_category,
                            preview_classification)
from app.categories import add_category, get_category
from app.files import add_file


def _seed(db):
    seed_defaults(db)


def test_seed_is_idempotent(db):
    seed_defaults(db)
    seed_defaults(db)
    names = [r["name"] for r in db.execute("SELECT name FROM categories ORDER BY id")]
    assert names.count("文档") == 1


def test_type_rule_suggests(db):
    _seed(db)
    f = add_file(db, "报告.pdf", "/报告.pdf")
    cat_id = suggest_category(db, f.id)
    assert get_category(db, cat_id).name == "文档"


def test_keyword_rule_wins_over_type(db):
    _seed(db)
    cat = add_category(db, "合同")
    add_rule(db, "keyword", "合同", cat.id)
    f = add_file(db, "房屋合同.pdf", "/房屋合同.pdf")
    assert suggest_category(db, f.id) == cat.id   # 关键词优先，不是"文档"


def test_no_extension_stays_none(db):
    _seed(db)
    f = add_file(db, "README", "/README")
    assert suggest_category(db, f.id) is None     # Review Focus #1


def test_preview_lists_uncategorized(db):
    _seed(db)
    f = add_file(db, "a.jpg", "/a.jpg")
    f2 = add_file(db, "b.png", "/b.png")
    prev = preview_classification(db)
    ids = {p["file_id"] for p in prev}
    assert f.id in ids and f2.id in ids
