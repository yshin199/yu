import tkinter.font as tkfont


def apply_theme(root):
    """应用深色主题（Sun Valley dark）与中文字体。"""
    try:
        import sv_ttk
        sv_ttk.set_theme("dark")
    except Exception:
        pass  # 未安装 sv_ttk 时退回系统默认主题

    try:
        for name, size in (("TkDefaultFont", 11), ("TkTextFont", 11),
                           ("TkMenuFont", 10), ("TkHeadingFont", 11)):
            f = tkfont.nametofont(name)
            f.configure(family="Microsoft YaHei UI", size=size)
    except Exception:
        pass