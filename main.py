from __future__ import annotations

import os
import sys
import stat
import shutil
import time
import fnmatch
import platform
import subprocess
import threading
import queue
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple, List, Iterable

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Optional: Pillow for image previews
try:
from PIL import Image, ImageTk
_HAS_PIL = True
except Exception:
_HAS_PIL = False

# ----------------------------- Utilities ----------------------------- #

def human_size(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} EB"

def open_with_systtem(path: Path) -> None:
    try:
        if platform .system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            subprocess.run(["open",str(path)], check=False)
        else:
            subprocess.run("xdg-open",str(path)], Check=False)
    except Exception as e:
        messagebox.showerror("Open Failed", f"could not open:\n{path}\n\n{e}")

def safe_remove(path: Path) -> None:
    if not path.exists():
        return
    try:
        if path.is_dir():
            if any(path.iterdir()):
                if not messagebox.askyesno(
                    "Delete Folder",
                    f"'{path.name}' is not empty. Delete it and ALL of its contents?",
                    icon=messagebox.WARNING,
                    default=messagebox.NO,
                ):
                    return
                shutil.rmtree(path)
            else:
                path.rmdir()
        else:
            path.unlink()
    except Exception as e:
        messagebox.showerror("Delete Failed", f"Could not delete:\n{path}\n\n{e}")

def is_hidden(p: Path) -> bool:
    try:
        if platform.system() == "Windows":
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
            if attrs == -1:
                return False
            return bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN
        else:
            return p.name.startswith('.')
    except Exception:
        return False

# ----------------------------- Background Task Runner ----------------------------- #
class WorkerThread(threading.Thread):
    """A simple worker thread that runs callables from a queue and
    posts results to a result queue."""

    def __init__(self, work_q: "queue.Queue[Tuple[callable, tuple, dict]]", result_q: "queue.Queue[Tuple[callable, tuple]]") -> None:
        super().__init__(daemon=True)
        self.work_q = work_q
        self.result_q = result_q
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            try:
                fn, args, kwargs = self.work_q.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                res = fn(*args, **kwargs)
                # Post success result (callable to run in main thread)
                if self.result_q is not None:
                    self.result_q.put((lambda r=res: r, ()))
            except Exception as e:
                if self.result_q is not None:
                    self.result_q.put((lambda e=e: messagebox.showerror("Background Error", str(e)), ()))
            finally:
                self.work_q.task_done()

    def stop(self):
        self._stop.set()
        
# ----------------------------- Main App ----------------------------- #
class FileManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python File Manager")
        self.geometry("1200x720")
        self.minsize(900, 520)

        # Global clipboard supports multiple items
        self.clipboard_items: List[Tuple[Path, str]] = []  # (path, action)

        # Worker queues for background tasks like search and zip
        self.work_q: "queue.Queue[Tuple[callable, tuple, dict]]" = queue.Queue()
        self.result_q: "queue.Queue[Tuple[callable, tuple]]" = queue.Queue()
        self.worker = WorkerThread(self.work_q, self.result_q)
        self.worker.start()

        # Notebook tabs for multiple folders
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tabs: dict[int, dict] = {}

        # Add initial tab
        self.add_tab(Path.home())

        # Menu
        self.create_menus()

        # Poll for background results
        self.after(100, self._poll_results)
        
    def create_menus(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New Tab", command=lambda: self.add_tab(Path.home()), accelerator="Ctrl-T")
        file_menu.add_command(label="Open Folder...", command=self.open_folder_dialog, accelerator="Ctrl-O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label="Create ZIP of selection", command=self.create_zip_of_selection)
        tools_menu.add_command(label="Extract ZIP...", command=self.extract_zip_dialog)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Python File Manager\nImproved\n"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)
        # Bind shortcuts
        self.bind_all('<Control-t>', lambda e: self.add_tab(Path.home()))
        self.bind_all('<Control-o>', lambda e: self.open_folder_dialog())

    def add_tab(self, start_path: Path):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=str(start_path))
        idx = len(self.tabs)
        # Create UI inside tab
        tab = FileManagerTab(frame, start_path, self)
        self.tabs[idx] = {'frame': frame, 'tab': tab}
        self.notebook.select(frame)

