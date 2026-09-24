import tkinter as tk

from app import classifier, db
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
