from database import init_db
from ui import DeviceSystemUI
import tkinter as tk

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = DeviceSystemUI(root)
    root.mainloop()