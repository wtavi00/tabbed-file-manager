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
