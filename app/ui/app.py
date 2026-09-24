import tkinter as tk
from tkinter import ttk

from .. import categories
from .documents import DocumentsView
from .home import HomeView


class App(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master)
        self.conn = conn
        self.pack(fill="both", expand=True)

        # 左栏导航
        self.left = ttk.Frame(self, padding=8)
        self.left.pack(side="left", fill="y")

        ttk.Label(self.left, text="导航").pack(anchor="w")
        ttk.Button(self.left, text="首页", command=self.show_home).pack(fill="x", pady=2)
        ttk.Button(self.left, text="文档管理", command=self.show_documents).pack(fill="x", pady=2)

        ttk.Label(self.left, text="分类").pack(anchor="w", pady=(12, 0))
        self.cat_tree = ttk.Treeview(self.left, show="tree", height=15)
        self.cat_tree.pack(fill="x")
        self.refresh_category_tree()

        # 内容区
        self.content = ttk.Frame(self, padding=8)
        self.content.pack(side="left", fill="both", expand=True)

        self.home_view = HomeView(self.content, self.conn)
        self.doc_view = DocumentsView(self.content, self.conn)
        self.current = None
        self.show_home()

    def refresh_category_tree(self):
        self.cat_tree.delete(*self.cat_tree.get_children())

        def add_nodes(nodes, parent=""):
            for n in nodes:
                item = self.cat_tree.insert(parent, "end", text=n["name"], values=(n["id"],))
                add_nodes(n["children"], item)

        add_nodes(categories.build_tree(self.conn))

    def show_home(self):
        self._switch(self.home_view)

    def show_documents(self):
        self._switch(self.doc_view)

    def _switch(self, view):
        if self.current is view:
            return
        if self.current is not None:
            self.current.pack_forget()
        self.current = view
        view.pack(fill="both", expand=True)
        view.refresh()
