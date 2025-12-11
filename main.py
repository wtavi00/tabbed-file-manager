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

