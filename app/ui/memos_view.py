import tkinter as tk
from tkinter import messagebox, ttk

from .. import memos

_TYPE_LABEL = {"note": "普通", "quick": "快速", "plan": "计划"}
_TYPE_KEY = {"普通备忘": "note", "快速备忘": "quick", "今日计划": "plan"}


class MemosView(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master)
        self.conn = conn
        self._editing_id = None
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=4)
        self.type_filter = tk.StringVar(value="全部")
        combo = ttk.Combobox(toolbar, textvariable=self.type_filter, state="readonly",
                             values=["全部", "普通备忘", "快速备忘", "今日计划"])
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Label(toolbar, text="搜索").pack(side="left", padx=(12, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(toolbar, textvariable=self.search_var, width=16).pack(side="left")
        ttk.Button(toolbar, text="新建备忘", command=self.new_memo).pack(side="left", padx=12)

        edit = ttk.Frame(self)
        edit.pack(fill="x", pady=4)
        ttk.Label(edit, text="标题").pack(side="left")
        self.title_var = tk.StringVar()
        ttk.Entry(edit, textvariable=self.title_var, width=40).pack(side="left", padx=4)
        ttk.Button(edit, text="保存", command=self.save_memo).pack(side="left", padx=4)

        self.content_text = tk.Text(self, height=5)
        self.content_text.pack(fill="x", pady=4)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=4)
        ttk.Button(actions, text="完成/取消", command=self.toggle_done).pack(side="left")
        ttk.Button(actions, text="置顶/取消", command=self.toggle_pin).pack(side="left")
        ttk.Button(actions, text="归档", command=self.archive).pack(side="left", padx=4)
        ttk.Button(actions, text="删除", command=self.delete).pack(side="left")

        self.tree = ttk.Treeview(self, columns=("title", "type", "state"), show="headings")
        self.tree.heading("title", text="标题")
        self.tree.heading("type", text="类型")
        self.tree.heading("state", text="状态")
        self.tree.column("title", width=360)
        self.tree.column("type", width=100)
        self.tree.column("state", width=160)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        mtype = _TYPE_KEY.get(self.type_filter.get())
        q = self.search_var.get().strip() or None
        items = memos.list_memos(self.conn, query=q, memo_type=mtype, archived=False)
        for i in self.tree.get_children():
            self.tree.delete(i)
        for m in items:
            state = []
            if m.done:
                state.append("已完成")
            if m.pinned:
                state.append("置顶")
            if m.memo_type == "plan" and m.plan_date:
                state.append(m.plan_date)
            self.tree.insert("", "end", iid=str(m.id), values=(
                m.title or "(无标题)",
                _TYPE_LABEL.get(m.memo_type, m.memo_type),
                "、".join(state) or "—"))

    def _selected(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def on_select(self, event):
        mid = self._selected()
        if mid is None:
            return
        m = memos.get_memo(self.conn, mid)
        if m:
            self._editing_id = mid
            self.title_var.set(m.title)
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", m.content)

    def new_memo(self):
        self._editing_id = None
        self.title_var.set("")
        self.content_text.delete("1.0", "end")

    def save_memo(self):
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        if not title and not content:
            return
        if self._editing_id is None:
            memos.add_memo(self.conn, title=title, content=content)
        else:
            memos.update_memo(self.conn, self._editing_id, title=title, content=content)
        self.refresh()

    def toggle_done(self):
        mid = self._selected()
        if mid is None:
            return
        m = memos.get_memo(self.conn, mid)
        if m:
            memos.set_memo_done(self.conn, mid, not m.done)
            self.refresh()

    def toggle_pin(self):
        mid = self._selected()
        if mid is None:
            return
        m = memos.get_memo(self.conn, mid)
        if m:
            memos.set_memo_pinned(self.conn, mid, not m.pinned)
            self.refresh()

    def archive(self):
        mid = self._selected()
        if mid is None:
            return
        memos.set_memo_archived(self.conn, mid, True)
        self.refresh()

    def delete(self):
        mid = self._selected()
        if mid is None:
            return
        if messagebox.askyesno("删除", "确定删除这条备忘？"):
            memos.delete_memo(self.conn, mid)
            self.refresh()
