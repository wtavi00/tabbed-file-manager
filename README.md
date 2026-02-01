# tabbed-file-manager
Cross-platform, Python-based file manager built with Tkinter. It includes features such as tabbed browsing, previews, multi-copy, ZIP extraction/creation, drag &amp; drop (internal), and background-task support.

## Features

### Core Functionality
- **Dual-Pane Interface**: Tree view for folder navigation and detailed file list with sorting
- **Multi-Tab Support**: Open multiple folders in separate tabs for easy comparison and organization
- **File Operations**: Copy, cut, paste, rename, delete, and create new folders
- **Drag & Drop**: Internal drag-and-drop support for moving files between folders
- **Search**: Background search with wildcard pattern matching across directories

### Advanced Features
- **ZIP Operations**: Create archives from selected files/folders and extract ZIP files
- **File Preview**: Built-in preview for images (with Pillow) and text files
- **Multi-Selection**: Perform operations on multiple files simultaneously
- **Smart Clipboard**: Copy/cut multiple items and paste them in any folder
- **Context Menu**: Right-click menu for quick access to common operations

### Navigation
- Back/Forward history navigation
- Up button to navigate to parent directory
- Address bar with direct path entry
- Tree view with expandable folder hierarchy

## Requirements

### Python Version
- Python 3.7 or higher

### Dependencies
- **tkinter** (usually included with Python)
- **Pillow** (optional, for image previews)
  ```bash
  pip install Pillow
  ```

## Installation

1. Clone or download the repository
2. Install optional dependencies:
   ```bash
   pip install Pillow
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Basic Operations

**Creating a New Folder**
- Click the "New Folder" button in the action bar
- Enter the folder name when prompted

**Renaming Files/Folders**
- Select an item and click "Rename"
- Or right-click and select "Rename" from the context menu

**Copying/Moving Files**
1. Select one or more items
2. Click "Copy" or "Cut"
3. Navigate to the destination folder
4. Click "Paste"

**Deleting Files/Folders**
- Select items and press Delete key
- Or click the "Delete" button
- Confirm the deletion when prompted

### Advanced Operations

**Creating ZIP Archives**
1. Select files/folders to archive
2. Go to Tools > Create ZIP of selection
3. Choose save location and filename

**Extracting ZIP Files**
1. Go to Tools > Extract ZIP
2. Select the ZIP file
3. Choose the extraction destination

**Searching for Files**
1. Click the "Search" button
2. Choose starting directory
3. Enter filename pattern (supports wildcards: `*.txt`, `file?.doc`)
4. Double-click results to navigate to the file location

**Using Multiple Tabs**
- Press `Ctrl+T` to open a new tab
- Press `Ctrl+O` to open a folder in a new tab
- Click the "File" menu for tab management options
   
### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | New tab |
| `Ctrl+O` | Open folder dialog |
| `Return` | Open selected file/folder |
| `Delete` | Delete selected items |
| `Double-click` | Open file/folder |
| `Right-click` | Show context menu |

## Platform Support

The file manager is cross-platform and supports:
- **Windows**: Full support with drive detection
- **macOS**: Full support with native file opening
- **Linux**: Full support with xdg-open integration

## File Structure
```
main.py
├── FileManagerApp (Main application class)
│   ├── Tab management
│   ├── Background task handling
│   └── Global clipboard
│
└── FileManagerTab (Individual tab class)
    ├── Tree view (folder hierarchy)
    ├── File list view
    ├── Preview pane
    ├── Navigation controls
    └── File operations
```

## Background Operations

The application uses a worker thread for time-consuming operations:
- **ZIP creation**: Archive files without freezing the UI
- **ZIP extraction**: Extract archives in the background
- **File search**: Search large directory trees asynchronously

## Known Limitations

- Image previews require Pillow to be installed
- Text file previews are limited to 200 KB
- Search results are capped at 5,000 items
- Hidden files are not shown (can be modified in code)
- Browser storage APIs (localStorage) are not used

## Troubleshooting

**Application won't start**
- Ensure Python 3.7+ is installed
- Verify tkinter is available: `python -m tkinter`
