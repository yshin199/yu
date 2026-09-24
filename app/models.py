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
