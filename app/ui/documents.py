import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .. import categories, classifier, files, organizer
from ..db import DEFAULT_ORGANIZE_DIR


class DocumentsView(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master)
        self.conn = conn
        self.category_id = None
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=4)
        ttk.Button(toolbar, text="登记文件", command=self.import_files).pack(side="left")
        ttk.Button(toolbar, text="扫描文件夹", command=self.scan_folder).pack(side="left")
        ttk.Button(toolbar, text="自动分类预览", command=self.auto_classify).pack(side="left")
        ttk.Button(toolbar, text="一键归入文件夹", command=self.organize).pack(side="left")
        ttk.Label(toolbar, text="搜索").pack(side="left", padx=(12, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(toolbar, textvariable=self.search_var, width=16).pack(side="left")

        ttk.Label(toolbar, text="归类到").pack(side="left", padx=(12, 0))
        self.cat_combo = ttk.Combobox(toolbar, state="readonly", width=12)
        self.cat_combo.pack(side="left")
        ttk.Button(toolbar, text="归类", command=self.assign_category).pack(side="left", padx=2)

        self.tree = ttk.Treeview(self, columns=("name", "type", "cat", "size"), show="headings")
        self.tree.heading("name", text="文件名")
        self.tree.heading("type", text="类型")
        self.tree.heading("cat", text="分类")
        self.tree.heading("size", text="大小")
        self.tree.column("name", width=320)
        self.tree.column("type", width=80)
        self.tree.column("cat", width=140)
        self.tree.column("size", width=90)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.open_file)

    def set_category(self, category_id):
        self.category_id = category_id

    def refresh(self):
        cats = categories.list_categories(self.conn)
        self._cat_map = {c.name: c.id for c in cats}
        self.cat_combo["values"] = list(self._cat_map.keys())

        q = self.search_var.get().strip() or None
        for item in self.tree.get_children():
            self.tree.delete(item)
        for f in files.list_files(self.conn, query=q, category_id=self.category_id,
                                  include_descendants=True):
            cat_name = ""
            if f.category_id is not None:
                c = categories.get_category(self.conn, f.category_id)
                cat_name = c.name if c else str(f.category_id)
            self.tree.insert("", "end", iid=str(f.id), values=(
                f.file_name, f.file_type, cat_name, f.size))

    def _selected_file_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def import_files(self):
        paths = filedialog.askopenfilenames(title="选择要登记的文件")
        for p in paths:
            files.add_file(self.conn, os.path.basename(p), p)
        self.refresh()

    def scan_folder(self):
        folder = filedialog.askdirectory(title="选择要扫描的文件夹")
        if not folder:
            return
        for root, _, fnames in os.walk(folder):
            for fn in fnames:
                files.add_file(self.conn, fn, os.path.join(root, fn))
        self.refresh()

    def auto_classify(self):
        preview = [p for p in classifier.preview_classification(self.conn)
                   if p["suggested_category_id"] is not None]
        if not preview:
            messagebox.showinfo("自动分类", "没有可自动分类的未分类文件")
            return
        by_id = {p["file_id"]: p["suggested_category_id"] for p in preview}
        top = tk.Toplevel(self)
        top.title("自动分类预览")
        top.geometry("640x420")
        top.transient(self.winfo_toplevel())
        ttk.Label(top, text="勾选要归类的内容，点「确认归类」应用（默认全选）").pack(
            anchor="w", padx=8, pady=4)
        tv = ttk.Treeview(top, columns=("name", "cat"), show="headings", selectmode="extended")
        tv.heading("name", text="文件")
        tv.heading("cat", text="建议分类")
        tv.column("name", width=400)
        tv.column("cat", width=160)
        tv.pack(fill="both", expand=True, padx=8, pady=4)
        for p in preview:
            c = categories.get_category(self.conn, p["suggested_category_id"])
            iid = str(p["file_id"])
            tv.insert("", "end", iid=iid, values=(p["file_name"], c.name if c else "?"))
            tv.selection_add(iid)

        def apply():
            for iid in tv.selection():
                fid = int(iid)
                files.set_file_category(self.conn, fid, by_id[fid])
            top.destroy()
            self.refresh()

        ttk.Button(top, text="确认归类", command=apply).pack(pady=6)

    def assign_category(self):
        fid = self._selected_file_id()
        name = self.cat_combo.get()
        if fid is None or not name:
            messagebox.showwarning("归类", "请先选中一个文件并选择分类")
            return
        files.set_file_category(self.conn, fid, self._cat_map[name])
        self.refresh()

    def organize(self):
        name = self.cat_combo.get()
        if not name:
            messagebox.showwarning("一键归入", "请先选择要归入的分类")
            return
        res = organizer.organize_category(self.conn, self._cat_map[name], DEFAULT_ORGANIZE_DIR)
        messagebox.showinfo(
            "一键归入",
            f"移动 {res['moved']} 个，跳过（源文件缺失）{res['skipped_missing']} 个")
        self.refresh()

    def open_file(self, event):
        fid = self._selected_file_id()
        if fid is None:
            return
        f = files.get_file(self.conn, fid)
        if f and os.path.exists(f.original_path):
            os.startfile(f.original_path)
        else:
            messagebox.showwarning("打开文件", "文件不存在或已被移动")
