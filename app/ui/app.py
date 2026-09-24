import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .. import backup, categories
from ..db import DEFAULT_DB_PATH
from .documents import DocumentsView
from .home import HomeView
from .memos_view import MemosView


class App(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master)
        self.conn = conn
        self.pack(fill="both", expand=True)
        self.selected_category_id = None

        # 左栏导航
        self.left = ttk.Frame(self, padding=8)
        self.left.pack(side="left", fill="y")

        ttk.Label(self.left, text="导航").pack(anchor="w")
        ttk.Button(self.left, text="首页", command=self.show_home).pack(fill="x", pady=2)
        ttk.Button(self.left, text="文档管理", command=self.show_documents).pack(fill="x", pady=2)
        ttk.Button(self.left, text="备忘笔记", command=self.show_memos).pack(fill="x", pady=2)

        ttk.Label(self.left, text="分类").pack(anchor="w", pady=(12, 0))
        self.cat_tree = ttk.Treeview(self.left, show="tree", height=12)
        self.cat_tree.pack(fill="x")
        self.cat_tree.bind("<ButtonRelease-1>", self._on_category_click)

        catbtns = ttk.Frame(self.left)
        catbtns.pack(fill="x", pady=4)
        ttk.Button(catbtns, text="新建", width=5, command=self.add_category).pack(side="left")
        ttk.Button(catbtns, text="子分类", width=7, command=self.add_subcategory).pack(side="left")
        ttk.Button(catbtns, text="重命名", width=7, command=self.rename_category).pack(side="left")
        ttk.Button(catbtns, text="删除", width=5, command=self.delete_category).pack(side="left")
        ttk.Button(catbtns, text="全部", width=5, command=self.clear_category_filter).pack(
            side="left", padx=(4, 0))

        ttk.Separator(self.left).pack(fill="x", pady=8)
        ttk.Label(self.left, text="数据与备份", anchor="w").pack(anchor="w")
        self.path_label = ttk.Label(self.left, text=str(DEFAULT_DB_PATH), foreground="#666",
                                    wraplength=170, justify="left")
        self.path_label.pack(anchor="w", pady=(2, 4))
        bkbtns = ttk.Frame(self.left)
        bkbtns.pack(fill="x")
        ttk.Button(bkbtns, text="导出备份", command=self.export_backup).pack(side="left", padx=(0, 4))
        ttk.Button(bkbtns, text="恢复备份", command=self.restore_backup).pack(side="left")

        self.refresh_category_tree()

        # 内容区
        self.content = ttk.Frame(self, padding=8)
        self.content.pack(side="left", fill="both", expand=True)

        self.home_view = HomeView(self.content, self.conn)
        self.doc_view = DocumentsView(self.content, self.conn)
        self.memo_view = MemosView(self.content, self.conn)
        self.current = None
        self.show_home()

    # ---- 分类树 ----
    def _selected_category_id(self):
        sel = self.cat_tree.selection()
        if not sel:
            return None
        vals = self.cat_tree.item(sel[0], "values")
        return int(vals[0]) if vals else None

    def refresh_category_tree(self):
        self.cat_tree.delete(*self.cat_tree.get_children())

        def add_nodes(nodes, parent=""):
            for n in nodes:
                item = self.cat_tree.insert(parent, "end", text=n["name"],
                                            values=(n["id"],), open=True)
                add_nodes(n["children"], item)

        add_nodes(categories.build_tree(self.conn))

    def _on_category_click(self, event):
        iid = self.cat_tree.identify_row(event.y)
        if not iid:
            # 点到分类树空白处 → 取消过滤
            self.clear_category_filter()
            return
        cid = self._selected_category_id()
        if cid is not None and cid == self.selected_category_id:
            # 再点一次已选中的分类 → 取消
            self.clear_category_filter()
        else:
            self.selected_category_id = cid
            self._refresh_current()

    def clear_category_filter(self):
        self.selected_category_id = None
        self.cat_tree.selection_remove(*self.cat_tree.selection())
        self._refresh_current()

    def _refresh_current(self):
        if self.current is self.doc_view:
            self.doc_view.set_category(self.selected_category_id)
            self.doc_view.refresh()
        elif self.current is self.memo_view:
            self.memo_view.set_category(self.selected_category_id)
            self.memo_view.refresh()

    # ---- 分类管理 ----
    def add_category(self):
        name = simpledialog.askstring("新建分类", "分类名称：", parent=self.winfo_toplevel())
        if name and name.strip():
            categories.add_category(self.conn, name.strip())
            self.refresh_category_tree()

    def add_subcategory(self):
        parent_id = self._selected_category_id()
        name = simpledialog.askstring("新建子分类", "子分类名称：", parent=self.winfo_toplevel())
        if name and name.strip():
            categories.add_category(self.conn, name.strip(), parent_id=parent_id)
            self.refresh_category_tree()

    def rename_category(self):
        cid = self._selected_category_id()
        if cid is None:
            messagebox.showwarning("重命名", "请先选中一个分类", parent=self.winfo_toplevel())
            return
        name = simpledialog.askstring("重命名", "新名称：", parent=self.winfo_toplevel())
        if name and name.strip():
            categories.rename_category(self.conn, cid, name.strip())
            self.refresh_category_tree()

    def delete_category(self):
        cid = self._selected_category_id()
        if cid is None:
            messagebox.showwarning("删除", "请先选中一个分类", parent=self.winfo_toplevel())
            return
        ok = messagebox.askyesno(
            "删除分类", "确定删除该分类及其子分类？\n其中的文件/备忘将变为未分类。",
            parent=self.winfo_toplevel())
        if ok:
            categories.delete_category(self.conn, cid)
            self.selected_category_id = None
            self.refresh_category_tree()
            self._refresh_current()

    # ---- 备份 ----
    def export_backup(self):
        dest = filedialog.asksaveasfilename(
            title="导出备份", defaultextension=".db",
            filetypes=[("数据库文件", "*.db")], parent=self.winfo_toplevel())
        if dest:
            backup.export_backup(self.conn, dest)
            messagebox.showinfo("备份", f"已导出到：\n{dest}", parent=self.winfo_toplevel())

    def restore_backup(self):
        src = filedialog.askopenfilename(
            title="选择备份文件", filetypes=[("数据库文件", "*.db")],
            parent=self.winfo_toplevel())
        if not src:
            return
        ok = messagebox.askyesno(
            "恢复备份", "恢复将覆盖当前所有数据，确定继续？", parent=self.winfo_toplevel())
        if ok:
            backup.restore_backup(self.conn, src)
            self.refresh_category_tree()
            self._refresh_current()
            messagebox.showinfo("恢复", "已恢复", parent=self.winfo_toplevel())

    # ---- 视图切换 ----
    def show_home(self):
        self._switch(self.home_view)

    def show_documents(self):
        self._switch(self.doc_view)

    def show_memos(self):
        self._switch(self.memo_view)

    def _switch(self, view):
        if self.current is view:
            return
        if self.current is not None:
            self.current.pack_forget()
        self.current = view
        view.pack(fill="both", expand=True)
        if view is self.doc_view:
            view.set_category(self.selected_category_id)
        elif view is self.memo_view:
            view.set_category(self.selected_category_id)
        view.refresh()
