from app.backup import export_backup, restore_backup
from app.categories import add_category, list_categories
from app.memos import add_memo


def test_export_and_restore(db, tmp_path):
    add_category(db, "工作")
    add_memo(db, title="备忘")
    backup_path = tmp_path / "backup.db"
    export_backup(db, backup_path)
    assert backup_path.exists()
    # 破坏当前库，再从备份恢复
    db.execute("DELETE FROM categories")
    db.execute("DELETE FROM memos")
    db.commit()
    restore_backup(db, backup_path)
    assert [c.name for c in list_categories(db)] == ["工作"]
    assert db.execute("SELECT COUNT(*) FROM memos").fetchone()[0] == 1
