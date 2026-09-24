import tkinter as tk
from datetime import date
from tkinter import ttk

from .. import memos, stats


class HomeView(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master)
        self.conn = conn
        self._build()

    def _build(self):
        # 今日计划
        plan_frame = ttk.LabelFrame(self, text="今日计划", padding=6)
        plan_frame.pack(fill="both", expand=True, pady=4)
        self.plan_entry = ttk.Entry(plan_frame)
        self.plan_entry.pack(fill="x")
        self.plan_entry.bind("<Return>", self._add_plan)
        self.plan_list = ttk.Frame(plan_frame)
        self.plan_list.pack(fill="both", expand=True)

        # 快速备忘
        quick_frame = ttk.LabelFrame(self, text="快速备忘", padding=6)
        quick_frame.pack(fill="both", expand=True, pady=4)
        self.quick_entry = ttk.Entry(quick_frame)
        self.quick_entry.pack(fill="x")
        self.quick_entry.bind("<Return>", self._add_quick)
        self.quick_list = ttk.Frame(quick_frame)
        self.quick_list.pack(fill="both", expand=True)

        # 摘要
        summary_frame = ttk.LabelFrame(self, text="模块摘要", padding=6)
        summary_frame.pack(fill="both", pady=4)
        self.summary_label = ttk.Label(summary_frame, text="", justify="left")
        self.summary_label.pack(anchor="w")

    def _add_plan(self, event):
        title = self.plan_entry.get().strip()
        if title:
            memos.add_memo(self.conn, title=title, memo_type="plan",
                           plan_date=date.today().isoformat())
            self.plan_entry.delete(0, "end")
            self.refresh()

    def _add_quick(self, event):
        content = self.quick_entry.get().strip()
        if content:
            memos.add_memo(self.conn, title=content, content=content, memo_type="quick")
            self.quick_entry.delete(0, "end")
            self.refresh()

    def _toggle_plan(self, memo_id):
        m = memos.get_memo(self.conn, memo_id)
        if m:
            memos.set_memo_done(self.conn, memo_id, not m.done)
            self.refresh()

    def refresh(self):
        today = date.today().isoformat()
        s = stats.home_summary(self.conn, today_iso=today)
        plans = memos.get_today_plans(self.conn, today)

        for w in self.plan_list.winfo_children():
            w.destroy()
        for m in plans:
            var = tk.BooleanVar(value=m.done)
            text = ("✓ " if m.done else "") + m.title
            cb = ttk.Checkbutton(self.plan_list, text=text, variable=var,
                                 command=lambda mid=m.id: self._toggle_plan(mid))
            cb.pack(anchor="w")
        if not plans:
            ttk.Label(self.plan_list, text="今天还没有计划").pack(anchor="w")

        for w in self.quick_list.winfo_children():
            w.destroy()
        quicks = memos.list_memos(self.conn, memo_type="quick", archived=False)[:5]
        for m in quicks:
            ttk.Label(self.quick_list, text="• " + m.title).pack(anchor="w")
        if not quicks:
            ttk.Label(self.quick_list, text="还没有快速备忘").pack(anchor="w")

        recent_files = ", ".join(f.file_name for f in s["recent_files"]) or "无"
        recent_memos = ", ".join(m.title for m in s["recent_memos"]) or "无"
        self.summary_label.config(text=(
            f"文档管理：共 {s['file_total']} 个文件，待分类 {s['file_uncategorized']} 个\n"
            f"备忘笔记：共 {s['memo_total']} 条备忘，未完成今日计划 {s['plan_incomplete']} 条\n"
            f"最近文件：{recent_files}\n"
            f"最近备忘：{recent_memos}"
        ))
