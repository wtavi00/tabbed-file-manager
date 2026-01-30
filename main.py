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

    def open_folder_dialog(self):
        d = filedialog.askdirectory(initialdir=str(Path.home()))
        if d:
            self.add_tab(Path(d))

    def create_zip_of_selection(self):
        tab = self._current_tab()
        if not tab:
            return
        sel = tab.current_selection()
        if not sel:
            messagebox.showinfo("ZIP", "Select items to archive.")
            return
        dest = filedialog.asksaveasfilename(defaultextension='.zip', filetypes=[('ZIP files', '*.zip')])
        if not dest:
            return
        dest_path = Path(dest)

        def do_zip():
            with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in sel:
                    if p.is_dir():
                        for root, dirs, files in os.walk(p):
                            for f in files:
                                fp = Path(root) / f
                                zf.write(fp, arcname=str(fp.relative_to(p.parent)))
                    else:
                        zf.write(p, arcname=str(p.name))
            return None

        self.work_q.put((do_zip, (), {}))
        messagebox.showinfo("ZIP", f"Creating {dest_path} in background.")

    def extract_zip_dialog(self):
        path = filedialog.askopenfilename(filetypes=[('ZIP files', '*.zip')])
        if not path:
            return
        dest = filedialog.askdirectory()
        if not dest:
            return
        pathp = Path(path)
        destp = Path(dest)

        def do_extract():
            with zipfile.ZipFile(pathp, 'r') as zf:
                zf.extractall(destp)
            return None

        self.work_q.put((do_extract, (), {}))
        messagebox.showinfo("Extract", f"Extracting {pathp} to {destp} in background.")
        
    def _current_tab(self) -> Optional['FileManagerTab']:
        if not self.notebook.tabs():
            return None
        cur = self.notebook.select()
        for info in self.tabs.values():
            if str(info['frame']) == cur:
                return info['tab']
        # fallback: match by index
        sel = self.notebook.index(cur)
        info = self.tabs.get(sel)
        if info:
            return info['tab']
        return None

    def _poll_results(self):
        try:
            while True:
                fn, args = self.result_q.get_nowait()
                try:
                    fn(*args)
                except Exception:
                    pass
                self.result_q.task_done()
        except queue.Empty:
            pass
        self.after(100, self._poll_results)

    def quit(self):
        try:
            self.worker.stop()
        except Exception:
            pass
        super().quit()

class FileManagerTab:
    def __init__(self, parent, start_path: Path, app: FileManagerApp):
        self.parent = parent
        self.app = app
        self.current_dir = start_path.resolve()
        self._history: List[Path] = []
        self._future: List[Path] = []
        self._list_cache: dict = {}

        # Layout: top toolbar, main paned (left tree / right main area)
        self.toolbar = ttk.Frame(parent, padding=(6, 6))
        self.toolbar.pack(fill=tk.X)

        self.btn_back = ttk.Button(self.toolbar, text="◀", width=3, command=self.go_back)
        self.btn_forward = ttk.Button(self.toolbar, text="▶", width=3, command=self.go_forward)
        self.btn_up = ttk.Button(self.toolbar, text="↑", width=3, command=self.go_up)
        self.btn_refresh = ttk.Button(self.toolbar, text="⟳", width=3, command=self.refresh)
        self.btn_back.pack(side=tk.LEFT, padx=2)
        self.btn_forward.pack(side=tk.LEFT, padx=2)
        self.btn_up.pack(side=tk.LEFT, padx=2)
        self.btn_refresh.pack(side=tk.LEFT, padx=6)

        ttk.Label(self.toolbar, text="Path:").pack(side=tk.LEFT)
        self.address_var = tk.StringVar(value=str(self.current_dir))
        self.address_entry = ttk.Entry(self.toolbar, textvariable=self.address_var)
        self.address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(self.toolbar, text="Go", command=self.go_to_address).pack(side=tk.LEFT, padx=4)

        # Main paned window
        main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Left: folder tree
        left = ttk.Frame(main_paned)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(left, columns=("#type",), displaycolumns=())
        self.tree.heading('#0', text='Folders')
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_open)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        tree_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll.grid(row=0, column=1, sticky='ns')
        main_paned.add(left, weight=1)

        # Right: notebook split between file list and preview
        right = ttk.Frame(main_paned)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        # Action bar for right pane
        action_bar = ttk.Frame(right)
        action_bar.grid(row=0, column=0, sticky='ew', pady=(4, 0))
        action_bar.columnconfigure(10, weight=1)
        
        ttk.Button(action_bar, text="New Folder", command=self.new_folder).grid(row=0, column=0, padx=2)
        ttk.Button(action_bar, text="Rename", command=self.rename_selected).grid(row=0, column=1, padx=2)
        ttk.Button(action_bar, text="Delete", command=self.delete_selected).grid(row=0, column=2, padx=2)
        ttk.Button(action_bar, text="Copy", command=lambda: self.copy_or_cut('copy')).grid(row=0, column=3, padx=2)
        ttk.Button(action_bar, text="Cut", command=lambda: self.copy_or_cut('cut')).grid(row=0, column=4, padx=2)
        ttk.Button(action_bar, text="Paste", command=self.paste_here).grid(row=0, column=5, padx=2)
        ttk.Button(action_bar, text="Open", command=self.open_selected).grid(row=0, column=6, padx=2)
        ttk.Button(action_bar, text="Search", command=self.open_search_dialog).grid(row=0, column=7, padx=2)

        # Split: list and preview
        inner_paned = ttk.PanedWindow(right, orient=tk.HORIZONTAL)
        inner_paned.grid(row=1, column=0, sticky='nsew')

        # File list
        list_frame = ttk.Frame(inner_paned)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.list = ttk.Treeview(list_frame, columns=("size", "type", "modified"), show='headings', selectmode='extended')
        self.list.heading('size', text='Size')
        self.list.heading('type', text='Type')
        self.list.heading('modified', text='Modified')
        
        self.list.column('size', width=100, anchor=tk.E)
        self.list.column('type', width=140, anchor=tk.W)
        self.list.column('modified', width=160, anchor=tk.W)
        
        self.list.bind('<Double-1>', lambda e: self.open_selected())
        self.list.bind('<Return>', lambda e: self.open_selected())
        self.list.bind('<Delete>', lambda e: self.delete_selected())
        self.list.bind('<<TreeviewSelect>>', lambda e: self.update_status())
        self.list.bind('<Button-3>', self.show_context_menu)
        
        # enable simple drag (start)
        self.list.bind('<ButtonPress-1>', self._on_list_button_press)
        self.list.bind('<B1-Motion>', self._on_list_b1_motion)
        self.list.bind('<ButtonRelease-1>', self._on_list_button_release)
        
        list_scroll_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.list.yview)
        list_scroll_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.list.xview)
        
        self.list.configure(yscrollcommand=list_scroll_y.set, xscrollcommand=list_scroll_x.set)
        self.list.grid(row=0, column=0, sticky='nsew')
        
        list_scroll_y.grid(row=0, column=1, sticky='ns')
        list_scroll_x.grid(row=1, column=0, sticky='ew')
        
        inner_paned.add(list_frame, weight=3)

        # Preview pane
        preview_frame = ttk.Frame(inner_paned)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(preview_frame, text='Preview', anchor='center')
        self.preview_label.grid(row=0, column=0, sticky='nsew')
        
        inner_paned.add(preview_frame, weight=2)

        main_paned.add(right, weight=3)
        
        # Status bar
        self.status_var = tk.StringVar(value='Ready')
        
        status = ttk.Label(parent, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN, padding=(8, 4))
        status.pack(fill=tk.X)

        # Context menu
        self.menu = tk.Menu(parent, tearoff=False)
        self.menu.add_command(label='Open', command=self.open_selected)
        
        self.menu.add_separator()
        
        self.menu.add_command(label='Copy', command=lambda: self.copy_or_cut('copy'))
        self.menu.add_command(label='Cut', command=lambda: self.copy_or_cut('cut'))
        self.menu.add_command(label='Paste', command=self.paste_here)
        
        self.menu.add_separator()
        
        self.menu.add_command(label='Rename', command=self.rename_selected)
        self.menu.add_command(label='Delete', command=self.delete_selected)
        self.menu.add_command(label='Create ZIP', command=self.create_zip_of_selection)

        # initialize tree and list
        self.populate_tree_root(self.current_dir)
        self.populate_list(self.current_dir)

        # Variables for drag
        self._drag_start_iid = None
        self._dragging = False
        
    # ----------------------- Tree methods ----------------------- #
    def populate_tree_root(self, focus_path: Path):
        self.tree.delete(*self.tree.get_children(''))
        try:
            if platform.system() == 'Windows':
                from string import ascii_uppercase
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for i, letter in enumerate(ascii_uppercase):
                    if bitmask & (1 << i):
                        drv = f"{letter}:/"
                        node = self.tree.insert('', 'end', text=drv, values=('drive',), open=False)
                        self.tree.insert(node, 'end', text='loading', values=('loading',))
            else:
                node = self.tree.insert('', 'end', text='/', values=('root',), open=True)
                self.tree.insert(node, 'end', text='loading', values=('loading',))
            self.expand_to_path(focus_path)
        except Exception:
            pass

    def expand_to_path(self, path: Path):
        parts = path.resolve().parts
        parent = ''
        if platform.system() == 'Windows':
            root_text = f"{Path(parts[0]).drive}/".replace('\\', '/')
            for n in self.tree.get_children(''):
                if self.tree.item(n, 'text').lower() == root_text.lower():
                    parent = n
                    break
            start_index = 1
        else:
            parent = self.tree.get_children('')[0]
            start_index = 1
        for p in parts[start_index:]:
            self.on_tree_open_node(parent)
            found = None
            for child in self.tree.get_children(parent):
                if self.tree.item(child, 'text') == p:
                    found = child
                    break
            if found is None:
                break
            parent = found
            self.tree.item(parent, open=True)
        try:
            self.tree.selection_set(parent)
            self.tree.see(parent)
        except Exception:
            pass

    def on_tree_open(self, event=None):
        node = self.tree.focus()
        self.on_tree_open_node(node)
        
    def on_tree_open_node(self, node):
        children = self.tree.get_children(node)
        if not children:
            return
        if self.tree.item(children[0], 'values') == ('loading',):
            self.tree.delete(children[0])
            base_path = self.get_node_path(node)
            try:
                entries = sorted([p for p in base_path.iterdir() if p.is_dir()], key=lambda x: x.name.lower())
            except Exception:
                entries = []
            for p in entries:
                if is_hidden(p):
                    continue
                sub = self.tree.insert(node, 'end', text=p.name, values=('dir',), open=False)
                self.tree.insert(sub, 'end', text='loading', values=('loading',))

    def on_tree_select(self, event=None):
        node = self.tree.focus()
        path = self.get_node_path(node)
        if path:
            self.navigate(path)

    def get_node_path(self, node) -> Optional[Path]:
        if not node:
            return None
        parts = []
        while node:
            text = self.tree.item(node, 'text')
            parts.insert(0, text)
            node = self.tree.parent(node)
        if platform.system() == 'Windows':
            p = Path(parts[0])
            for seg in parts[1:]:
                p = p / seg
            return p
        else:
            p = Path('/'
                     )
            for seg in parts[1:]:
                p = p / seg
            return p


    # ----------------------- List methods ----------------------- #
    def populate_list(self, directory: Path):
        # Use caching to avoid re-statting too often
        try:
            self.list.delete(*self.list.get_children(''))
            entries = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except Exception as e:
            messagebox.showerror('Access Denied', f'Cannot access folder:\n{directory}\n\n{e}')
            return

        # Batch insert for performance
        for p in entries:
            if is_hidden(p):
                continue
            try:
                st = p.stat()
                mod = time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))
                if p.is_dir():
                    size = '<DIR>'
                    typ = 'Folder'
                else:
                    size = human_size(st.st_size)
                    typ = p.suffix[1:].upper() + ' File' if p.suffix else 'File'
                safe_iid = str(p).replace('\\', '/')
                self.list.insert('', 'end', iid=safe_iid, values=(size, typ, mod), text=p.name)
            except Exception:
                pass
        self.update_status()

    def current_selection(self) -> List[Path]:
        items = self.list.selection()
        return [Path(iid.replace('/', os.sep)) for iid in items]

    # ----------------------------- Actions ----------------------------- #
    def show_context_menu(self, event):
        try:
            iid = self.list.identify_row(event.y)
            if iid:
                self.list.selection_set(iid)
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self.menu.grab_release()
            except Exception:
                pass

    def new_folder(self):
        name = simpledialog.askstring('New Folder', 'Folder name:', parent=self.parent)
        if not name:
            return
        target = self.current_dir / name
        try:
            target.mkdir(parents=False, exist_ok=False)
            self.refresh()
        except Exception as e:
            messagebox.showerror('Create Failed', f'Could not create folder:\n{target}\n\n{e}')

    def rename_selected(self):
        sel = self.current_selection()
        if not sel:
            messagebox.showinfo('Rename', 'Select a file or folder to rename.')
            return
        src = sel[0]
        new_name = simpledialog.askstring('Rename', f"New name for '{src.name}':", initialvalue=src.name, parent=self.parent)
        if not new_name:
            return
        dst = src.parent / new_name
        try:
            src.rename(dst)
            self.refresh()
        except Exception as e:
            messagebox.showerror('Rename Failed', f'Could not rename:\n{src}\n→ {dst}\n\n{e}')

    def delete_selected(self):
        sel = self.current_selection()
        if not sel:
            messagebox.showinfo('Delete', 'Select one or more items to delete.')
            return
        names = '\n'.join(p.name for p in sel[:10])
        extra = '\n...' if len(sel) > 10 else ''
        if not messagebox.askyesno('Confirm Delete', f'Delete {len(sel)} item(s)?\n\n{names}{extra}', icon=messagebox.WARNING, default=messagebox.NO):
            return
        for p in sel:
            safe_remove(p)
        self.refresh()

    def delete_selected(self):
        sel = self.current_selection()
        if not sel:
            messagebox.showinfo('Delete', 'Select one or more items to delete.')
            return
        names = '\n'.join(p.name for p in sel[:10])
        extra = '\n...' if len(sel) > 10 else ''
        if not messagebox.askyesno('Confirm Delete', f'Delete {len(sel)} item(s)?\n\n{names}{extra}', icon=messagebox.WARNING, default=messagebox.NO):
            return
        for p in sel:
            safe_remove(p)
        self.refresh()
        
