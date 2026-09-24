import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from .. import categories, memos

_TYPE_LABEL = {"note": "普通", "quick": "快速", "plan": "计划"}
_TYPE_KEY = {"普通备忘": "note", "快速备忘": "quick", "今日计划": "plan"}
_TYPE_NAME = {"note": "普通备忘", "quick": "快速备忘", "plan": "今日计划"}


class MemosView(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master)
        self.conn = conn
        self.category_id = None
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
        self.show_archived = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="显示已归档", variable=self.show_archived,
                        command=self.refresh).pack(side="left", padx=8)
        ttk.Button(toolbar, text="新建备忘", command=self.new_memo).pack(side="left", padx=12)

        edit1 = ttk.Frame(self)
        edit1.pack(fill="x", pady=4)
        ttk.Label(edit1, text="类型").pack(side="left")
        self.edit_type = tk.StringVar(value="普通备忘")
        ttk.Combobox(edit1, textvariable=self.edit_type, state="readonly",
                     values=["普通备忘", "快速备忘", "今日计划"], width=10).pack(side="left", padx=4)
        ttk.Label(edit1, text="分类").pack(side="left")
        self.edit_category = tk.StringVar(value="未分类")
        self.cat_combo = ttk.Combobox(edit1, textvariable=self.edit_category,
                                      state="readonly", width=12)
        self.cat_combo.pack(side="left", padx=4)
        ttk.Label(edit1, text="日期").pack(side="left")
        self.edit_date = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(edit1, textvariable=self.edit_date, width=12).pack(side="left", padx=4)

        edit2 = ttk.Frame(self)
        edit2.pack(fill="x", pady=4)
        ttk.Label(edit2, text="标题").pack(side="left")
        self.title_var = tk.StringVar()
        ttk.Entry(edit2, textvariable=self.title_var, width=40).pack(side="left", padx=4)
        ttk.Button(edit2, text="保存", command=self.save_memo).pack(side="left", padx=4)

        self.content_text = tk.Text(self, height=5)
        self.content_text.pack(fill="x", pady=4)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=4)
        ttk.Button(actions, text="完成/取消", command=self.toggle_done).pack(side="left")
        ttk.Button(actions, text="置顶/取消", command=self.toggle_pin).pack(side="left")
        ttk.Button(actions, text="归档", command=self.archive).pack(side="left", padx=4)
        ttk.Button(actions, text="取消归档", command=self.unarchive).pack(side="left")
        ttk.Button(actions, text="删除", command=self.delete).pack(side="left", padx=4)

        self.tree = ttk.Treeview(self, columns=("title", "type", "state"), show="headings")
        self.tree.heading("title", text="标题")
        self.tree.heading("type", text="类型")
        self.tree.heading("state", text="状态")
        self.tree.column("title", width=360)
        self.tree.column("type", width=100)
        self.tree.column("state", width=180)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def set_category(self, category_id):
        self.category_id = category_id

    def refresh(self):
        cats = categories.list_categories(self.conn)
        self._cat_map = {"未分类": None}
        for c in cats:
            self._cat_map[c.name] = c.id
        self.cat_combo["values"] = list(self._cat_map.keys())

        mtype = _TYPE_KEY.get(self.type_filter.get())
        q = self.search_var.get().strip() or None
        archived = None if self.show_archived.get() else False
        items = memos.list_memos(self.conn, query=q, memo_type=mtype,
                                 archived=archived, category_id=self.category_id)
        for i in self.tree.get_children():
            self.tree.delete(i)
        for m in items:
            state = []
            if m.done:
                state.append("已完成")
            if m.pinned:
                state.append("置顶")
            if m.archived:
                state.append("已归档")
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
            self.edit_type.set(_TYPE_NAME.get(m.memo_type, "普通备忘"))
            cat_name = "未分类"
            if m.category_id is not None:
                c = categories.get_category(self.conn, m.category_id)
                cat_name = c.name if c else "未分类"
            self.edit_category.set(cat_name)
            self.edit_date.set(m.plan_date or date.today().isoformat())

    def new_memo(self):
        self._editing_id = None
        self.title_var.set("")
        self.content_text.delete("1.0", "end")
        self.edit_type.set("普通备忘")
        self.edit_category.set("未分类")
        self.edit_date.set(date.today().isoformat())

    def save_memo(self):
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        if not title and not content:
            return
        cat_id = self._cat_map.get(self.edit_category.get())
        if self._editing_id is None:
            mtype = _TYPE_KEY.get(self.edit_type.get(), "note")
            plan_date = self.edit_date.get().strip() if mtype == "plan" else None
            memos.add_memo(self.conn, title=title, content=content, memo_type=mtype,
                           category_id=cat_id, plan_date=plan_date)
        else:
            memos.update_memo(self.conn, self._editing_id, title=title, content=content)
            memos.set_memo_category(self.conn, self._editing_id, cat_id)
            if _TYPE_KEY.get(self.edit_type.get()) == "plan":
                memos.update_memo(self.conn, self._editing_id,
                                  plan_date=self.edit_date.get().strip())
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

    def unarchive(self):
        mid = self._selected()
        if mid is None:
            return
        memos.set_memo_archived(self.conn, mid, False)
        self.refresh()

    def delete(self):
        mid = self._selected()
        if mid is None:
            return
        if messagebox.askyesno("删除", "确定删除这条备忘？"):
            memos.delete_memo(self.conn, mid)
            self.refresh()
