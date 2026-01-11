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
