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
        self.filter_label = ttk.Label(toolbar, text="全部文件", foreground="#9e9e9e")
        self.filter_label.pack(side="left", padx=(12, 0))

        self.tree = ttk.Treeview(self, columns=("name", "type", "cat", "size"),
                                 show="headings", selectmode="extended")
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
        self.tree.bind("<Button-3>", self._on_right_click)

        self.menu = tk.Menu(self, tearoff=0)
        self.cat_submenu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="手动分类", menu=self.cat_submenu)
        self.menu.add_command(label="自动分类", command=self.auto_classify_selected)
        self.menu.add_separator()
        self.menu.add_command(label="删除", command=self.delete_selected)

        # 左键按住拖动多选
        self._drag_active = False
        self._drag_anchor = None
        self.tree.bind("<ButtonPress-1>", self._drag_press)
        self.tree.bind("<B1-Motion>", self._drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._drag_release)

    def set_category(self, category_id):
        self.category_id = category_id

    def refresh(self):
        cats = categories.list_categories(self.conn)
        self._cat_map = {c.name: c.id for c in cats}
        self.cat_combo["values"] = list(self._cat_map.keys())
        if self.category_id is not None:
            c = categories.get_category(self.conn, self.category_id)
            self.filter_label.config(text=f"当前分类：{c.name if c else self.category_id}")
        else:
            self.filter_label.config(text="全部文件")

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

    def _selected_file_ids(self):
        return [int(i) for i in self.tree.selection()]

    def _assign_ids(self, ids, category_id):
        for fid in ids:
            files.set_file_category(self.conn, fid, category_id)
        self.refresh()

    def _auto_classify_ids(self, ids):
        assigned = 0
        for fid in ids:
            sid = classifier.suggest_category(self.conn, fid)
            if sid is not None:
                files.set_file_category(self.conn, fid, sid)
                assigned += 1
        self.refresh()
        return assigned, len(ids) - assigned

    def _delete_ids(self, ids):
        for fid in ids:
            files.delete_file_entry(self.conn, fid)
        self.refresh()

    # ---- 右键菜单 ----
    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and iid not in self.tree.selection():
            self.tree.selection_set(iid)
        self._rebuild_cat_submenu()
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _rebuild_cat_submenu(self):
        self.cat_submenu.delete(0, "end")
        self.cat_submenu.add_command(label="未分类", command=lambda: self._assign_selected(None))
        for c in categories.list_categories(self.conn):
            self.cat_submenu.add_command(
                label=c.name, command=lambda cid=c.id: self._assign_selected(cid))

    def _assign_selected(self, category_id):
        ids = self._selected_file_ids()
        if ids:
            self._assign_ids(ids, category_id)

    def auto_classify_selected(self):
        ids = self._selected_file_ids()
        if not ids:
            messagebox.showinfo("自动分类", "请先选中文件")
            return
        assigned, unmatched = self._auto_classify_ids(ids)
        messagebox.showinfo("自动分类", f"已归类 {assigned} 个，{unmatched} 个无匹配规则")

    def delete_selected(self):
        ids = self._selected_file_ids()
        if not ids:
            return
        if messagebox.askyesno("删除", f"确定删除 {len(ids)} 个文件的登记？\n（电脑里的真实文件不会被删除）"):
            self._delete_ids(ids)

    # ---- 左键拖动多选 ----
    def _select_range(self, start_iid, end_iid):
        children = self.tree.get_children()
        if start_iid not in children or end_iid not in children:
            return
        i0 = children.index(start_iid)
        i1 = children.index(end_iid)
        lo, hi = sorted((i0, i1))
        self.tree.selection_remove(*self.tree.selection())
        for iid in children[lo:hi + 1]:
            self.tree.selection_add(iid)

    def _drag_press(self, event):
        row = self.tree.identify_row(event.y)
        if row == "":
            self._drag_active = False
            self.tree.selection_remove(*self.tree.selection())
            return "break"
        self._drag_active = True
        self._drag_anchor = row
        self.tree.selection_set(row)
        return "break"

    def _drag_motion(self, event):
        if not self._drag_active:
            return None
        row = self.tree.identify_row(event.y)
        if row == "":
            return "break"
        self._select_range(self._drag_anchor, row)
        return "break"

    def _drag_release(self, event):
        self._drag_active = False
        return None

    def import_files(self):
        paths = filedialog.askopenfilenames(title="选择要登记的文件")
        if not paths:
            return
        self._register_paths(paths)
        messagebox.showinfo("登记", f"已登记 {len(paths)} 个文件")

    def _register_paths(self, paths):
        for p in paths:
            files.add_file(self.conn, os.path.basename(p), p, category_id=self.category_id)
        self.refresh()

    def scan_folder(self):
        folder = filedialog.askdirectory(title="选择要扫描的文件夹")
        if not folder:
            return
        collected = []
        for root, _, fnames in os.walk(folder):
            for fn in fnames:
                collected.append(os.path.join(root, fn))
        if collected:
            self._register_paths(collected)
            messagebox.showinfo("扫描", f"已扫描登记 {len(collected)} 个文件")

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
