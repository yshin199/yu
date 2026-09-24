# 本地文档管理桌面软件 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个运行在本机的文档/文件 + 备忘桌面软件（独立窗口，非浏览器），数据本地持久化。

**Architecture:** 纯 Python 核心逻辑层（数据模型、SQLite 存储、分类树、文件操作、自动分类、统计、备份）+ 薄 Tkinter UI 层。核心逻辑与 UI 完全分离，核心层用 pytest 做单元测试；UI 层只做渲染和调用核心函数，配冒烟测试。真实文件的"一键归入文件夹"通过 `shutil.move` 实现，路径可注入以便测试。

**Tech Stack:** Python 3.14 · Tkinter（标准库）· sqlite3（标准库）· pytest 9.1.1

**Spec:** `PRD.md`（需求与验收标准）；`docs/superpowers/specs/2026-09-24-document-manager-design.md`（技术设计）

> 说明：PRD 第 8 节写的是 "Electron 打包成 .exe"。本计划改用 **Python + Tkinter + SQLite**：本机已装 Python 3.14，tkinter 与 sqlite3 均为标准库，零重量级下载、核心逻辑可干净测试；运行后仍是"双击打开独立窗口、不经过浏览器"。.exe 打包（PyInstaller）留作以后。功能需求与验收标准不变。

## Global Constraints

- Python 3.14；只允许标准库（tkinter/sqlite3/pathlib/datetime/shutil/json/typing）+ pytest（仅测试用）。
- 数据目录固定在用户主目录下：`~/文档管理数据/`，数据库文件 `app.db`，整理根目录 `~/文档管理数据/文件库/`（均不在代码仓库内）。
- 所有时间用 ISO 格式字符串（`datetime.now().isoformat(timespec="seconds")`；日期用 `YYYY-MM-DD`）。
- 备忘类型取值固定为 `note` / `quick` / `plan`；文件条目 `status` 为 `indexed` / `organized`。
- 删除分类时：删除该分类及其全部子孙分类；其中的文件/备忘的 `category_id` 置为 NULL（未分类），不删除文件/备忘。
- 测试一律通过 `python -m pytest tests/ -q` 运行；禁止删测试、跳过、改断言来"通过"。

## Review Focus

以下输入/场景最可能让真实用户踩坑，每个都要有用例锁住：

1. **无扩展名文件名**（如 `README`）→ `infer_type` 返回空串，不匹配任何类型规则，文件保持未分类，不崩溃。
2. **一键归入时源文件已不存在**（被移走/删除）→ 跳过并计入 skipped，不崩溃、不误报成功。
3. **一键归入时目标重名** → 加序号后缀 ` (1)`、` (2)`，绝不覆盖已有文件。
4. **删除有子分类/有内容的分类** → 子孙一并删、内容回到未分类，数据不丢失。
5. **首次运行/空库** → 应用以空状态正常启动，首页显示 0，不崩溃。

## File Structure

```
文档管理/
├── PRD.md
├── docs/superpowers/plans/2026-09-24-document-manager.md   # 本计划
├── .gitignore
├── main.py                 # 入口：建库、seed 默认、开窗口
├── 启动文档管理.bat          # 双击启动（pythonw）
├── app/
│   ├── __init__.py
│   ├── models.py           # Category / FileEntry / Memo / Rule dataclasses
│   ├── db.py               # connect / init_schema / 默认路径常量
│   ├── categories.py       # 分类树增删改查、descendants、path、tree
│   ├── files.py            # 文件条目 CRUD、infer_type、organize_category
│   ├── memos.py            # 备忘 CRUD、今日计划、置顶、归档
│   ├── classifier.py       # 默认分类/类型规则、seed、规则 CRUD、suggest/preview
│   ├── stats.py            # home_summary
│   ├── backup.py           # export / restore
│   └── ui/
│       ├── __init__.py
│       ├── app.py          # App 主窗口：左导航 + 内容区 + 分类树
│       ├── home.py         # HomeView
│       ├── documents.py    # DocumentsView
│       └── memos_view.py   # MemosView
└── tests/
    ├── conftest.py         # tmp db fixture + tk root fixture
    ├── test_models.py
    ├── test_db.py
    ├── test_categories.py
    ├── test_files.py
    ├── test_memos.py
    ├── test_classifier.py
    ├── test_stats.py
    ├── test_backup.py
    └── test_ui_smoke.py
```

---

### Task 1: 项目骨架 + 数据模型 + git 初始化

**Files:**
- Create: `.gitignore`, `app/__init__.py`, `app/models.py`, `tests/conftest.py`, `tests/test_models.py`

**Interfaces:**
- Produces: `app.models.Category`, `FileEntry`, `Memo`, `Rule` dataclass（字段见下）；`tests/conftest.py` 的 `db` fixture（返回已建表的 sqlite3 连接，见 Task 2 落地前的临时实现）。

- [ ] **Step 1: 写失败测试**

`tests/test_models.py`:
```python
from app.models import Category, FileEntry, Memo, Rule

def test_category_defaults():
    c = Category(id=1, name="工作")
    assert c.parent_id is None
    assert c.sort_order == 0

def test_file_entry_defaults():
    f = FileEntry(id=1, file_name="a.pdf", original_path="/x/a.pdf")
    assert f.file_type == ""          # 由 files.infer_type 单独推断，模型不管
    assert f.category_id is None
    assert f.status == "indexed"

def test_memo_defaults():
    m = Memo(id=1, title="t", content="c")
    assert m.memo_type == "note"
    assert m.pinned is False and m.done is False and m.archived is False

def test_rule_fields():
    r = Rule(id=1, kind="type", match_value="pdf", target_category_id=2)
    assert r.enabled is True
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_models.py -q`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.models'`）

- [ ] **Step 3: 写最小实现**

`app/__init__.py`（空文件）。
`app/models.py`:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Category:
    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0

@dataclass
class FileEntry:
    id: int
    file_name: str
    original_path: str
    file_type: str = ""
    category_id: Optional[int] = None
    note: str = ""
    size: int = 0
    created_at: str = ""
    status: str = "indexed"

@dataclass
class Memo:
    id: int
    title: str = ""
    content: str = ""
    memo_type: str = "note"
    category_id: Optional[int] = None
    pinned: bool = False
    done: bool = False
    archived: bool = False
    plan_date: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Rule:
    id: int
    kind: str
    match_value: str
    target_category_id: int
    enabled: bool = True
```

`.gitignore`:
```
__pycache__/
*.pyc
.pytest_cache/
文档管理数据/
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_models.py -q`
Expected: PASS

- [ ] **Step 5: 初始化 git 并提交**

```bash
git init
git add .gitignore app/__init__.py app/models.py tests/test_models.py
git commit -m "chore: 项目骨架与数据模型"
```

---

### Task 2: 数据库层（connect + schema）

**Files:**
- Create: `app/db.py`, `tests/test_db.py`
- Modify: `tests/conftest.py`（落地 `db` fixture）

**Interfaces:**
- Produces:
  - `app.db.DEFAULT_DB_PATH = Path.home() / "文档管理数据" / "app.db"`
  - `app.db.DEFAULT_ORGANIZE_DIR = Path.home() / "文档管理数据" / "文件库"`
  - `app.db.connect(db_path=DEFAULT_DB_PATH) -> sqlite3.Connection`（`row_factory=sqlite3.Row`，自动建父目录）
  - `app.db.init_schema(conn) -> None`（建 4 张表，幂等）

- [ ] **Step 1: 写失败测试**

`tests/test_db.py`:
```python
from app import db

def test_connect_creates_parent(tmp_path):
    p = tmp_path / "sub" / "app.db"
    conn = db.connect(p)
    conn.close()
    assert p.exists()

def test_init_schema_creates_tables(tmp_path):
    conn = db.connect(tmp_path / "a.db")
    db.init_schema(conn)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"categories", "files", "memos", "rules"} <= names

def test_init_schema_is_idempotent(tmp_path):
    conn = db.connect(tmp_path / "b.db")
    db.init_schema(conn)
    db.init_schema(conn)  # 不抛异常
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_db.py -q`
Expected: FAIL（`No module named 'app.db'`）

- [ ] **Step 3: 写实现**

`app/db.py`:
```python
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
```

`tests/conftest.py`（覆盖 Task 1 的临时版）:
```python
import pytest
from app import db

@pytest.fixture
def db(tmp_path):
    conn = db.connect(tmp_path / "test.db")
    db.init_schema(conn)
    yield conn
    conn.close()
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_db.py tests/test_models.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/db.py tests/test_db.py tests/conftest.py
git commit -m "feat: 数据库连接与建表"
```

---

### Task 3: 分类树操作

**Files:**
- Create: `app/categories.py`, `tests/test_categories.py`

**Interfaces:**
- Consumes: `db` fixture（已建表）
- Produces:
  - `add_category(conn, name, parent_id=None) -> Category`
  - `get_category(conn, category_id) -> Category | None`
  - `list_categories(conn) -> list[Category]`
  - `list_children(conn, parent_id=None) -> list[Category]`
  - `rename_category(conn, category_id, name) -> None`
  - `get_descendant_ids(conn, category_id) -> list[int]`
  - `delete_category(conn, category_id) -> None`
  - `category_path(conn, category_id) -> list[str]`
  - `build_tree(conn) -> list[dict]`

- [ ] **Step 1: 写失败测试**

`tests/test_categories.py`:
```python
from app.categories import (
    add_category, get_category, list_children, rename_category,
    delete_category, get_descendant_ids, category_path, build_tree,
)

def test_add_and_get(db):
    c = add_category(db, "工作")
    assert c.id is not None
    assert get_category(db, c.id).name == "工作"

def test_hierarchy(db):
    work = add_category(db, "工作")
    contract = add_category(db, "合同", parent_id=work.id)
    kids = list_children(db, work.id)
    assert [k.name for k in kids] == ["合同"]
    assert contract.parent_id == work.id

def test_rename(db):
    c = add_category(db, "旧名")
    rename_category(db, c.id, "新名")
    assert get_category(db, c.id).name == "新名"

def test_descendants(db):
    a = add_category(db, "a")
    b = add_category(db, "b", a.id)
    c = add_category(db, "c", b.id)
    ids = set(get_descendant_ids(db, a.id))
    assert ids == {a.id, b.id, c.id}

def test_delete_reassigns_items(db):
    work = add_category(db, "工作")
    db.execute("INSERT INTO files (file_name, original_path, category_id) VALUES (?,?,?)",
               ("a.pdf", "/a.pdf", work.id))
    db.execute("INSERT INTO memos (title, content, category_id) VALUES (?,?,?)",
               ("m", "x", work.id))
    db.commit()
    delete_category(db, work.id)
    assert get_category(db, work.id) is None
    assert db.execute("SELECT category_id FROM files").fetchone()[0] is None
    assert db.execute("SELECT category_id FROM memos").fetchone()[0] is None

def test_delete_cascades_children(db):
    a = add_category(db, "a")
    add_category(db, "b", a.id)
    delete_category(db, a.id)
    assert list_children(db, a.id) == []

def test_category_path(db):
    a = add_category(db, "工作")
    b = add_category(db, "合同", a.id)
    assert category_path(db, b.id) == ["工作", "合同"]

def test_build_tree(db):
    a = add_category(db, "工作")
    add_category(db, "合同", a.id)
    tree = build_tree(db)
    assert tree[0]["name"] == "工作"
    assert tree[0]["children"][0]["name"] == "合同"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_categories.py -q`
Expected: FAIL（`No module named 'app.categories'`）

- [ ] **Step 3: 写实现**

`app/categories.py`（row→Category 用 `dict(row)` 解包）:
```python
from typing import Optional
from .models import Category

def _to(cat_row):
    if cat_row is None:
        return None
    d = dict(cat_row)
    return Category(**d)

def add_category(conn, name, parent_id=None, sort_order=0):
    cur = conn.execute(
        "INSERT INTO categories (name, parent_id, sort_order) VALUES (?,?,?)",
        (name, parent_id, sort_order))
    conn.commit()
    return get_category(conn, cur.lastrowid)

def get_category(conn, category_id):
    row = conn.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()
    return _to(row)

def list_categories(conn):
    rows = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    return [_to(r) for r in rows]

def list_children(conn, parent_id=None):
    if parent_id is None:
        rows = conn.execute(
            "SELECT * FROM categories WHERE parent_id IS NULL ORDER BY sort_order, id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories WHERE parent_id=? ORDER BY sort_order, id",
            (parent_id,)).fetchall()
    return [_to(r) for r in rows]

def rename_category(conn, category_id, name):
    conn.execute("UPDATE categories SET name=? WHERE id=?", (name, category_id))
    conn.commit()

def get_descendant_ids(conn, category_id):
    seen, frontier = [], [category_id]
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.append(cur)
        for row in conn.execute(
                "SELECT id FROM categories WHERE parent_id=?", (cur,)).fetchall():
            frontier.append(row["id"])
    return seen

def delete_category(conn, category_id):
    ids = get_descendant_ids(conn, category_id)
    ph = ",".join("?" * len(ids))
    conn.execute(f"UPDATE files SET category_id=NULL WHERE category_id IN ({ph})", ids)
    conn.execute(f"UPDATE memos SET category_id=NULL WHERE category_id IN ({ph})", ids)
    conn.execute(f"DELETE FROM categories WHERE id IN ({ph})", ids)
    conn.commit()

def category_path(conn, category_id):
    names = []
    cur = category_id
    while cur is not None:
        row = conn.execute("SELECT * FROM categories WHERE id=?", (cur,)).fetchone()
        if row is None:
            break
        names.append(row["name"])
        cur = row["parent_id"]
    return list(reversed(names))

def build_tree(conn):
    cats = list_categories(conn)
    by_parent = {}
    for c in cats:
        by_parent.setdefault(c.parent_id, []).append(c)
    def node(c):
        return {"id": c.id, "name": c.name,
                "children": [node(k) for k in by_parent.get(c.id, [])]}
    return [node(c) for c in by_parent.get(None, [])]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_categories.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/categories.py tests/test_categories.py
git commit -m "feat: 分类树增删改查"
```

---

### Task 4: 文件条目操作 + 类型推断

**Files:**
- Create: `app/files.py`, `tests/test_files.py`

**Interfaces:**
- Consumes: `db` fixture；`app.models.FileEntry`
- Produces:
  - `infer_type(file_name) -> str`（小写扩展名，无点；无扩展名返回 ""）
  - `add_file(conn, file_name, original_path, size=0, category_id=None) -> FileEntry`
  - `get_file(conn, file_id) -> FileEntry | None`
  - `set_file_category(conn, file_id, category_id) -> None`
  - `set_file_note(conn, file_id, note) -> None`
  - `delete_file_entry(conn, file_id) -> None`（只删索引，不动真实文件）
  - `list_files(conn, category_id=None, query=None, file_type=None, include_descendants=False) -> list[FileEntry]`

- [ ] **Step 1: 写失败测试**

`tests/test_files.py`:
```python
from app.files import (infer_type, add_file, get_file, set_file_category,
                       set_file_note, delete_file_entry, list_files)

def test_infer_type():
    assert infer_type("a.pdf") == "pdf"
    assert infer_type("B.JPG") == "jpg"
    assert infer_type("archive.tar.gz") == "gz"
    assert infer_type("README") == ""          # Review Focus #1

def test_add_and_get(db):
    f = add_file(db, "报告.pdf", "/docs/报告.pdf", size=100)
    assert f.file_type == "pdf"
    assert f.status == "indexed"
    assert f.category_id is None
    assert get_file(db, f.id).file_name == "报告.pdf"

def test_set_category_and_note(db):
    f = add_file(db, "a.txt", "/a.txt")
    set_file_category(db, f.id, 9)
    set_file_note(db, f.id, "说明")
    g = get_file(db, f.id)
    assert g.category_id == 9 and g.note == "说明"

def test_list_files_filters(db):
    a = add_file(db, "a.pdf", "/a.pdf")
    add_file(db, "b.jpg", "/b.jpg")
    db.execute("INSERT INTO categories (name) VALUES ('文档')")
    db.commit()
    set_file_category(db, a.id, 1)
    # 按分类过滤
    assert [f.id for f in list_files(db, category_id=1)] == [a.id]
    # 按类型过滤
    assert len(list_files(db, file_type="jpg")) == 1
    # 按文件名搜索
    assert len(list_files(db, query="b")) == 1

def test_delete_entry_keeps_file(db):
    f = add_file(db, "a.txt", "/a.txt")
    delete_file_entry(db, f.id)
    assert get_file(db, f.id) is None
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_files.py -q`
Expected: FAIL（`No module named 'app.files'`）

- [ ] **Step 3: 写实现**

`app/files.py`:
```python
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import FileEntry

def _now():
    return datetime.now().isoformat(timespec="seconds")

def _to(row):
    if row is None:
        return None
    d = dict(row)
    return FileEntry(**d)

def infer_type(file_name):
    return Path(file_name).suffix.lower().lstrip(".")

def add_file(conn, file_name, original_path, size=0, category_id=None):
    cur = conn.execute(
        "INSERT INTO files (file_name, original_path, file_type, category_id, size, created_at, status) "
        "VALUES (?,?,?,?,?,?,?)",
        (file_name, str(original_path), infer_type(file_name), category_id, size, _now(), "indexed"))
    conn.commit()
    return get_file(conn, cur.lastrowid)

def get_file(conn, file_id):
    return _to(conn.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone())

def set_file_category(conn, file_id, category_id):
    conn.execute("UPDATE files SET category_id=? WHERE id=?", (category_id, file_id))
    conn.commit()

def set_file_note(conn, file_id, note):
    conn.execute("UPDATE files SET note=? WHERE id=?", (note, file_id))
    conn.commit()

def delete_file_entry(conn, file_id):
    conn.execute("DELETE FROM files WHERE id=?", (file_id,))
    conn.commit()

def list_files(conn, category_id=None, query=None, file_type=None, include_descendants=False):
    sql = "SELECT * FROM files WHERE 1=1"
    params = []
    if category_id is not None:
        if include_descendants:
            from .categories import get_descendant_ids
            ids = get_descendant_ids(conn, category_id)
            sql += f" AND category_id IN ({','.join('?'*len(ids))})"
            params += ids
        else:
            sql += " AND category_id=?"
            params.append(category_id)
    if query:
        sql += " AND file_name LIKE ?"
        params.append(f"%{query}%")
    if file_type:
        sql += " AND file_type=?"
        params.append(file_type)
    sql += " ORDER BY created_at DESC, id DESC"
    return [_to(r) for r in conn.execute(sql, params).fetchall()]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_files.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/files.py tests/test_files.py
git commit -m "feat: 文件条目 CRUD 与类型推断"
```

---

### Task 5: 备忘操作

**Files:**
- Create: `app/memos.py`, `tests/test_memos.py`

**Interfaces:**
- Consumes: `db` fixture；`app.models.Memo`
- Produces:
  - `add_memo(conn, title="", content="", memo_type="note", category_id=None, plan_date=None) -> Memo`
  - `get_memo(conn, memo_id) -> Memo | None`
  - `update_memo(conn, memo_id, title=None, content=None, category_id=None, plan_date=None) -> None`
  - `set_memo_done(conn, memo_id, done) -> None`
  - `set_memo_pinned(conn, memo_id, pinned) -> None`
  - `set_memo_archived(conn, memo_id, archived) -> None`
  - `delete_memo(conn, memo_id) -> None`
  - `list_memos(conn, query=None, memo_type=None, archived=None, category_id=None) -> list[Memo]`
  - `get_today_plans(conn, date_iso) -> list[Memo]`

- [ ] **Step 1: 写失败测试**

`tests/test_memos.py`:
```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_memos.py -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/memos.py`（`list_memos` 默认按 pinned DESC、created_at DESC；`archived=None` 表示不过滤）:
```python
from datetime import datetime
from .models import Memo

def _now():
    return datetime.now().isoformat(timespec="seconds")

def _to(row):
    if row is None:
        return None
    d = dict(row)
    return Memo(**{k: (bool(v) if k in ("pinned", "done", "archived") else v) for k, v in d.items()})

def add_memo(conn, title="", content="", memo_type="note", category_id=None, plan_date=None):
    ts = _now()
    cur = conn.execute(
        "INSERT INTO memos (title, content, memo_type, category_id, plan_date, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (title, content, memo_type, category_id, plan_date, ts, ts))
    conn.commit()
    return get_memo(conn, cur.lastrowid)

def get_memo(conn, memo_id):
    return _to(conn.execute("SELECT * FROM memos WHERE id=?", (memo_id,)).fetchone())

def update_memo(conn, memo_id, title=None, content=None, category_id=None, plan_date=None):
    sets, params = [], []
    if title is not None:
        sets.append("title=?"); params.append(title)
    if content is not None:
        sets.append("content=?"); params.append(content)
    if category_id is not None:
        sets.append("category_id=?"); params.append(category_id)
    if plan_date is not None:
        sets.append("plan_date=?"); params.append(plan_date)
    if sets:
        sets.append("updated_at=?"); params.append(_now())
        params.append(memo_id)
        conn.execute(f"UPDATE memos SET {', '.join(sets)} WHERE id=?", params)
        conn.commit()

def set_memo_done(conn, memo_id, done):
    conn.execute("UPDATE memos SET done=?, updated_at=? WHERE id=?", (1 if done else 0, _now(), memo_id))
    conn.commit()

def set_memo_pinned(conn, memo_id, pinned):
    conn.execute("UPDATE memos SET pinned=?, updated_at=? WHERE id=?", (1 if pinned else 0, _now(), memo_id))
    conn.commit()

def set_memo_archived(conn, memo_id, archived):
    conn.execute("UPDATE memos SET archived=?, updated_at=? WHERE id=?", (1 if archived else 0, _now(), memo_id))
    conn.commit()

def delete_memo(conn, memo_id):
    conn.execute("DELETE FROM memos WHERE id=?", (memo_id,))
    conn.commit()

def list_memos(conn, query=None, memo_type=None, archived=None, category_id=None):
    sql = "SELECT * FROM memos WHERE 1=1"
    params = []
    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params += [f"%{query}%", f"%{query}%"]
    if memo_type:
        sql += " AND memo_type=?"; params.append(memo_type)
    if archived is not None:
        sql += " AND archived=?"; params.append(1 if archived else 0)
    if category_id is not None:
        sql += " AND category_id=?"; params.append(category_id)
    sql += " ORDER BY pinned DESC, created_at DESC, id DESC"
    return [_to(r) for r in conn.execute(sql, params).fetchall()]

def get_today_plans(conn, date_iso):
    rows = conn.execute(
        "SELECT * FROM memos WHERE memo_type='plan' AND plan_date=? AND archived=0 "
        "ORDER BY done ASC, created_at ASC, id ASC", (date_iso,)).fetchall()
    return [_to(r) for r in rows]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_memos.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/memos.py tests/test_memos.py
git commit -m "feat: 备忘 CRUD 与今日计划"
```

---

### Task 6: 自动分类

**Files:**
- Create: `app/classifier.py`, `tests/test_classifier.py`

**Interfaces:**
- Consumes: `db` fixture；`app.categories.add_category`；`app.files.add_file`
- Produces:
  - `DEFAULT_CATEGORIES = ["文档", "图片", "表格", "视频", "音频", "压缩包", "程序"]`
  - `DEFAULT_TYPE_RULES = {"pdf":"文档","doc":"文档","docx":"文档","txt":"文档","md":"文档","jpg":"图片","jpeg":"图片","png":"图片","gif":"图片","bmp":"图片","svg":"图片","xls":"表格","xlsx":"表格","csv":"表格","mp4":"视频","mov":"视频","avi":"视频","mkv":"视频","mp3":"音频","wav":"音频","zip":"压缩包","rar":"压缩包","7z":"压缩包","exe":"程序","msi":"程序"}`
  - `seed_defaults(conn) -> None`（默认分类不存在则建；默认类型规则不存在则建，幂等）
  - `add_rule(conn, kind, match_value, target_category_id) -> Rule`
  - `list_rules(conn) -> list[Rule]`
  - `delete_rule(conn, rule_id) -> None`
  - `suggest_category(conn, file_id) -> int | None`（关键词规则优先于类型规则）
  - `preview_classification(conn) -> list[dict]`

- [ ] **Step 1: 写失败测试**

`tests/test_classifier.py`:
```python
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
    cat = add_category(db, "图片")
    f2 = add_file(db, "b.png", "/b.png")
    prev = preview_classification(db)
    ids = {p["file_id"] for p in prev}
    assert f.id in ids and f2.id in ids
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_classifier.py -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/classifier.py`:
```python
from .models import Rule

DEFAULT_CATEGORIES = ["文档", "图片", "表格", "视频", "音频", "压缩包", "程序"]
DEFAULT_TYPE_RULES = {
    "pdf": "文档", "doc": "文档", "docx": "文档", "txt": "文档", "md": "文档",
    "jpg": "图片", "jpeg": "图片", "png": "图片", "gif": "图片", "bmp": "图片", "svg": "图片",
    "xls": "表格", "xlsx": "表格", "csv": "表格",
    "mp4": "视频", "mov": "视频", "avi": "视频", "mkv": "视频",
    "mp3": "音频", "wav": "音频",
    "zip": "压缩包", "rar": "压缩包", "7z": "压缩包",
    "exe": "程序", "msi": "程序",
}

def seed_defaults(conn):
    from .categories import add_category, list_categories
    existing = {c.name for c in list_categories(conn)}
    name_to_id = {}
    for name in DEFAULT_CATEGORIES:
        if name not in existing:
            cat = add_category(conn, name)
            name_to_id[name] = cat.id
        else:
            name_to_id[name] = next(
                c.id for c in list_categories(conn) if c.name == name)
    have = {(r["kind"], r["match_value"]) for r in conn.execute(
        "SELECT kind, match_value FROM rules WHERE kind='type'")}
    for ext, cat_name in DEFAULT_TYPE_RULES.items():
        if ("type", ext) not in have:
            conn.execute(
                "INSERT INTO rules (kind, match_value, target_category_id, enabled) VALUES (?,?,?,1)",
                ("type", ext, name_to_id[cat_name]))
    conn.commit()

def add_rule(conn, kind, match_value, target_category_id):
    cur = conn.execute(
        "INSERT INTO rules (kind, match_value, target_category_id, enabled) VALUES (?,?,?,1)",
        (kind, match_value, target_category_id))
    conn.commit()
    row = conn.execute("SELECT * FROM rules WHERE id=?", (cur.lastrowid,)).fetchone()
    d = dict(row)
    return Rule(**{**d, "enabled": bool(d["enabled"])})

def list_rules(conn):
    rows = conn.execute("SELECT * FROM rules ORDER BY id").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        out.append(Rule(**{**d, "enabled": bool(d["enabled"])}))
    return out

def delete_rule(conn, rule_id):
    conn.execute("DELETE FROM rules WHERE id=?", (rule_id,))
    conn.commit()

def _matching_rule(conn, file_entry):
    rules = list_rules(conn)
    keywords = [r for r in rules if r.enabled and r.kind == "keyword"]
    types = [r for r in rules if r.enabled and r.kind == "type"]
    for r in keywords:                       # 关键词优先
        if r.match_value and r.match_value in file_entry.file_name:
            return r
    for r in types:
        if file_entry.file_type and r.match_value.lower() == file_entry.file_type.lower():
            return r
    return None

def suggest_category(conn, file_id):
    from .files import get_file
    f = get_file(conn, file_id)
    if f is None:
        return None
    r = _matching_rule(conn, f)
    return r.target_category_id if r else None

def preview_classification(conn):
    rows = conn.execute(
        "SELECT * FROM files WHERE category_id IS NULL ORDER BY id").fetchall()
    out = []
    for row in rows:
        d = dict(row)
        from .models import FileEntry
        f = FileEntry(**d)
        sid = _matching_rule(conn, f)
        out.append({
            "file_id": f.id, "file_name": f.file_name,
            "suggested_category_id": sid.target_category_id if sid else None,
        })
    return out
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_classifier.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/classifier.py tests/test_classifier.py
git commit -m "feat: 自动分类规则与预览"
```

---

### Task 7: 首页统计

**Files:**
- Create: `app/stats.py`, `tests/test_stats.py`

**Interfaces:**
- Consumes: `db` fixture；`app.files`、`app.memos`
- Produces: `home_summary(conn, today_iso=None, recent_limit=5) -> dict`，键：`file_total`(int)、`file_uncategorized`(int)、`recent_files`(list[FileEntry])、`plan_incomplete`(int)、`memo_total`(int)、`recent_memos`(list[Memo])

- [ ] **Step 1: 写失败测试**

`tests/test_stats.py`:
```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_stats.py -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/stats.py`:
```python
from .models import FileEntry, Memo

def _files(rows):
    return [FileEntry(**dict(r)) for r in rows]

def _memos(rows):
    return [Memo(**{k: (bool(v) if k in ("pinned","done","archived") else v)
                    for k, v in dict(r).items()}) for r in rows]

def home_summary(conn, today_iso=None, recent_limit=5):
    file_total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    file_unc = conn.execute("SELECT COUNT(*) FROM files WHERE category_id IS NULL").fetchone()[0]
    recent_files = _files(conn.execute(
        "SELECT * FROM files ORDER BY created_at DESC, id DESC LIMIT ?", (recent_limit,)).fetchall())
    memo_total = conn.execute("SELECT COUNT(*) FROM memos WHERE archived=0").fetchone()[0]
    plan_incomplete = 0
    if today_iso is not None:
        plan_incomplete = conn.execute(
            "SELECT COUNT(*) FROM memos WHERE memo_type='plan' AND plan_date=? "
            "AND archived=0 AND done=0", (today_iso,)).fetchone()[0]
    recent_memos = _memos(conn.execute(
        "SELECT * FROM memos WHERE archived=0 ORDER BY created_at DESC, id DESC LIMIT ?",
        (recent_limit,)).fetchall())
    return {
        "file_total": file_total, "file_uncategorized": file_unc,
        "recent_files": recent_files, "plan_incomplete": plan_incomplete,
        "memo_total": memo_total, "recent_memos": recent_memos,
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_stats.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/stats.py tests/test_stats.py
git commit -m "feat: 首页统计"
```

---

### Task 8: 一键归入真实文件夹

**Files:**
- Create: `app/organizer.py`, `tests/test_organizer.py`

**Interfaces:**
- Consumes: `db` fixture；`app.categories.category_path`；`app.files.get_file`
- Produces: `organize_category(conn, category_id, root_dir) -> dict`，键：`moved`、`skipped_missing`、`skipped_collision`（int）。仅处理该分类**直接**的、`status='indexed'` 的文件；成功移动后更新 `original_path` 与 `status='organized'`。

- [ ] **Step 1: 写失败测试**

`tests/test_organizer.py`:
```python
from app.organizer import organize_category
from app.categories import add_category
from app.files import add_file, get_file

def _touch(p, text=b""):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text)

def test_moves_files(db, tmp_path):
    src1 = tmp_path / "src" / "a.pdf"; _touch(src1, b"1")
    src2 = tmp_path / "src" / "b.pdf"; _touch(src2, b"2")
    cat = add_category(db, "文档")
    add_file(db, "a.pdf", src1, category_id=cat.id)
    add_file(db, "b.pdf", src2, category_id=cat.id)
    root = tmp_path / "out"
    res = organize_category(db, cat.id, root)
    assert res["moved"] == 2
    assert (root / "文档" / "a.pdf").exists()
    assert (root / "文档" / "b.pdf").exists()
    assert not src1.exists()

def test_missing_source_skipped(db, tmp_path):
    cat = add_category(db, "文档")
    f = add_file(db, "gone.pdf", tmp_path / "no" / "gone.pdf", category_id=cat.id)
    res = organize_category(db, cat.id, tmp_path / "out")
    assert res["moved"] == 0 and res["skipped_missing"] == 1      # Review Focus #2
    assert get_file(db, f.id).status == "indexed"

def test_collision_gets_suffix(db, tmp_path):
    src = tmp_path / "s" / "a.pdf"; _touch(src, b"x")
    cat = add_category(db, "文档")
    add_file(db, "a.pdf", src, category_id=cat.id)
    root = tmp_path / "out"
    (root / "文档").mkdir(parents=True)
    (root / "文档" / "a.pdf").write_bytes(b"existing")
    res = organize_category(db, cat.id, root)
    assert res["moved"] == 1
    assert (root / "文档" / "a (1).pdf").exists()                 # Review Focus #3
    assert (root / "文档" / "a.pdf").read_bytes() == b"existing"  # 不覆盖
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_organizer.py -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/organizer.py`:
```python
import shutil
from pathlib import Path
from .categories import category_path
from .files import get_file

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
    moved = skipped_missing = 0
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
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_organizer.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/organizer.py tests/test_organizer.py
git commit -m "feat: 一键归入真实文件夹"
```

---

### Task 9: 备份与恢复

**Files:**
- Create: `app/backup.py`, `tests/test_backup.py`

**Interfaces:**
- Consumes: `db` fixture
- Produces:
  - `export_backup(conn, dest_path) -> str`（返回 dest_path；用 sqlite backup API 写完整副本）
  - `restore_backup(conn, source_path) -> None`（把 source 内容覆盖进 conn，替换现有数据）

- [ ] **Step 1: 写失败测试**

`tests/test_backup.py`:
```python
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
    db.execute("DELETE FROM categories"); db.execute("DELETE FROM memos"); db.commit()
    restore_backup(db, backup_path)
    assert [c.name for c in list_categories(db)] == ["工作"]
    assert db.execute("SELECT COUNT(*) FROM memos").fetchone()[0] == 1
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_backup.py -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/backup.py`:
```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_backup.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/backup.py tests/test_backup.py
git commit -m "feat: 备份与恢复"
```

---

### Task 10: 主窗口 + 首页视图 + 入口

**Files:**
- Create: `main.py`, `app/ui/__init__.py`, `app/ui/app.py`, `app/ui/home.py`, `tests/test_ui_smoke.py`
- Modify: `tests/conftest.py`（加 tk root fixture）

**Interfaces:**
- Consumes: 全部核心模块
- Produces:
  - `main.main()`：建库→seed→开 `App`
  - `app.ui.app.App(root, conn)`：左导航（首页/文档/备忘按钮 + 分类树 `ttk.Treeview`）+ 右侧内容区，`show_home()` / `show_documents()` / `show_memos()` 切换
  - `app.ui.home.HomeView(parent, conn)`：`refresh()` 渲染今日计划、快速备忘、摘要

- [ ] **Step 1: 写冒烟测试**

`tests/conftest.py` 追加:
```python
import tkinter as tk

@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()
```

`tests/test_ui_smoke.py`:
```python
from app.ui.app import App
from app.ui.home import HomeView
from app import classifier

def test_app_builds(root, db):
    classifier.seed_defaults(db)
    app = App(root, db)
    app.show_home()
    root.update()
    assert app.winfo_exists()

def test_home_view_builds(root, db):
    classifier.seed_defaults(db)
    view = HomeView(root, db)
    view.refresh()
    root.update()
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_ui_smoke.py -q`
Expected: FAIL（`No module named 'app.ui.app'`）

- [ ] **Step 3: 写实现**

`main.py`:
```python
import tkinter as tk
from app import db, classifier
from app.ui.app import App

def main():
    conn = db.connect()
    db.init_schema(conn)
    classifier.seed_defaults(conn)
    root = tk.Tk()
    root.title("文档管理")
    root.geometry("1100x720")
    App(root, conn)
    root.mainloop()

if __name__ == "__main__":
    main()
```

`app/ui/__init__.py`（空）。

`app/ui/app.py`：`App` 持有 `conn`，用 `ttk.Frame` 左栏 + 内容 `ttk.Frame`；左栏三个 `ttk.Button`（首页/文档管理/备忘笔记）＋分类 `ttk.Treeview`（用 `categories.build_tree` 填充）；右侧切换三个视图实例。提供 `show_home/show_documents/show_memos` 与 `refresh_category_tree`。

`app/ui/home.py`：`HomeView(ttk.Frame)`，`refresh()` 里调用 `stats.home_summary(conn, today_iso=date.today().isoformat())` 与 `memos.get_today_plans`，用 `ttk.Label`/`ttk.Treeview` 显示三块；顶部提供"新增今日计划"输入框与"新增快速备忘"输入框，回车即 `memos.add_memo` 后 `refresh()`。

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_ui_smoke.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add main.py app/ui tests/test_ui_smoke.py tests/conftest.py
git commit -m "feat: 主窗口与首页"
```

---

### Task 11: 文档管理视图

**Files:**
- Create: `app/ui/documents.py`；扩充 `tests/test_ui_smoke.py`

**Interfaces:**
- Consumes: `app.files`、`app.categories`、`app.classifier`、`app.organizer`
- Produces: `app.ui.documents.DocumentsView(parent, conn)`：文件列表（`ttk.Treeview`）、登记文件按钮（`filedialog.askopenfilenames`/`askdirectory` 扫描）、手动分类（右键或下拉）、自动分类预览按钮、一键归入按钮、双击打开原文件（`os.startfile`）

- [ ] **Step 1: 写冒烟测试**

`tests/test_ui_smoke.py` 追加:
```python
from app.ui.documents import DocumentsView

def test_documents_view_builds(root, db):
    view = DocumentsView(root, db)
    view.refresh()
    root.update()
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_ui_smoke.py::test_documents_view_builds -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/ui/documents.py`：`DocumentsView(ttk.Frame)`，含工具栏（登记文件/扫描文件夹/自动分类预览/一键归入）＋文件 `ttk.Treeview`（列：文件名/类型/分类/大小）+ 备注编辑。`refresh()` 用 `files.list_files` 填充；"自动分类预览"用 `classifier.preview_classification` 弹确认框，确认后逐条 `files.set_file_category`；"一键归入"用 `organizer.organize_category(conn, 当前分类, db.DEFAULT_ORGANIZE_DIR)` 并 `messagebox` 报结果。

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_ui_smoke.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/ui/documents.py tests/test_ui_smoke.py
git commit -m "feat: 文档管理视图"
```

---

### Task 12: 备忘视图

**Files:**
- Create: `app/ui/memos_view.py`；扩充 `tests/test_ui_smoke.py`

**Interfaces:**
- Consumes: `app.memos`、`app.categories`
- Produces: `app.ui.memos_view.MemosView(parent, conn)`：备忘列表（普通/快速/今日计划三个入口）、编辑区（标题+正文）、勾选完成、置顶、归档、搜索

- [ ] **Step 1: 写冒烟测试**

`tests/test_ui_smoke.py` 追加:
```python
from app.ui.memos_view import MemosView

def test_memos_view_builds(root, db):
    view = MemosView(root, db)
    view.refresh()
    root.update()
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_ui_smoke.py::test_memos_view_builds -q`
Expected: FAIL

- [ ] **Step 3: 写实现**

`app/ui/memos_view.py`：`MemosView(ttk.Frame)`，列表用 `ttk.Treeview`（列：标题/类型/分类/状态），上方类型切换 + 搜索框 + 新建按钮；右侧或下方编辑区保存即 `memos.add_memo`/`update_memo`；勾选/置顶/归档按钮分别调 `set_memo_done/pinned/archived` 后 `refresh()`。

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_ui_smoke.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/ui/memos_view.py tests/test_ui_smoke.py
git commit -m "feat: 备忘视图"
```

---

### Task 13: 启动器 + 全量回归

**Files:**
- Create: `启动文档管理.bat`

**Interfaces:**
- Consumes: `main.py`

- [ ] **Step 1: 写启动器**

`启动文档管理.bat`:
```bat
@echo off
cd /d "%~dp0"
start "" pythonw main.py
```

- [ ] **Step 2: 运行全部测试**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS（不得删测试、跳过或改断言）

- [ ] **Step 3: 提交**

```bash
git add 启动文档管理.bat
git commit -m "chore: 启动器"
```

---

## 完成后的最终验证

```bash
python -m pytest tests/ -q
```
预期：所有测试通过。再手动验证 PRD 第 10 节验收标准（启动、数据持久化、分类、文档、备忘、首页、备份恢复）逐条可过。
