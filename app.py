import sys
import os
import re # Added for filename sanitization
from datetime import datetime
import fnmatch
from typing import List, Tuple, Dict, Any, Optional, Set
from functools import partial # For connecting signals with arguments

# Import PyQt6 modules
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeView, QSizePolicy, QLabel, QTextEdit,
    QFileDialog, QGroupBox, QDialog, QMessageBox, QAbstractItemView, QMenu
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QDesktopServices, QFont, QBrush
from PyQt6.QtCore import Qt, QDir, QModelIndex, QFileSystemWatcher, QSettings, QUrl, QSize

# --- Constants ---
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# QSettings constants
ORGANIZATION_NAME = "YourOrganizationName" # Change as you see fit
APPLICATION_NAME = "ProjectContextGenerator"
SETTINGS_PINNED_DIRS = "pinnedDirectories"
SETTINGS_RECENT_DIRS = "recentDirectories"
MAX_PINNED_DIRS = 3
MAX_RECENT_DIRS = 3

# --- Color Palette ---
COLORS: Dict[str, str] = {
    # Base/Backgrounds
    "background": "#0F1015",
    "cardBackground": "#1E1F26",
    "groupBoxBackground": "#16171D",
    "focusBackground": "#22232B",
    "treeViewAlternateBg": "#22232B",

    # Text Colors
    "textPrimary": "#FFFFFF",
    "textSecondary": "#B0B3C1",
    "disabledText": "#707380",

    # Primary/Accent Colors
    "primaryBlue": "#3B82F6",
    "lightBlue": "#4FC3F7",
    "primaryRed": "#FF4C61",

    # Borders
    "borderDark": "#292A32",
    "borderLight": "#25262D", # Used for readonly, slightly lighter
    "buttonBorder": "#353640",
    "buttonHoverBorder": "#40414B",
    "disabledBorder": "#2A2B35",
    "generateButtonDarkBlue": "#306ABD", # Darker blue for generate button border
    "clearButtonRedBorder": "#5C2E33", # Reddish border for clear button

    # Button Backgrounds
    "buttonNormalBg": "#282930",
    "buttonHoverBg": "#303138",
    "buttonPressedBg": "#18191F",
    "disabledBg": "#1F2027",
    "clearButtonBg": "#3A2024", # Darker red base for clear button
    "clearButtonHoverBg": "#5C2E33", # Lighter red on hover for clear button
    "clearButtonPressedBg": "#2A181B", # Darkest red when pressed for clear button

    # Scrollbar
    "scrollHandleNormal": "#4A4B55",
    "scrollHandleBorder": "#5A5C67",

    # Other
    "clearButtonHoverText": "#FF7F8C", # Lighter text on hover for clear button
}


# Directories to exclude (lowercase, set for efficient lookup)
EXCLUDE_DIRS: Set[str] = {
    '.git', '.idea', 'venv', '__pycache__', 'node_modules', '.vscode',
    'target', 'build', 'dist', 'out', '.gradle', '.mvn', '.venv', '.mypy_cache', '.pytest_cache',
    '.ruff_cache', 'env', '.env', 'bower_components', 'jspm_packages',
    'bin', 'obj', 'packages', 'logs', 'temp', 'tmp', '.terraform', '.terragrunt-cache',
    '.angular', '.cache', 'coverage', 'docs_build', 'site', 'local_env',
    '.serverless', '.dynamodb', '.localstack', '.vagrant', '.kitchen', '.next', '.nuxt',
    'vendor', # Common for PHP/Ruby
}
# Files to exclude (lowercase)
EXCLUDE_FILES_EXACT: Set[str] = {
    '.ds_store', 'thumbs.db', '.gitignore', 'pipfile.lock',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock',
    'npm-debug.log', 'yarn-debug.log', 'yarn.error.log', '.npmrc', '.babelrc', '.eslintrc.js', '.eslintrc.json', '.eslintrc.yaml', '.eslintrc.yml', '.eslintrc', '.prettierrc.js', '.prettierrc.json', '.prettierrc.yaml', '.prettierrc.yml', '.prettierrc',
    'pytest.ini', 'tox.ini', 'setup.cfg', 'pyproject.toml',
    '.editorconfig', '.gitattributes', '.gitmodules',
    'web.config', 'app.config', '.env.local', '.env.development', '.env.production', '.env.test',
    'nohup.out',
}
EXCLUDE_FILES_PATTERNS: List[str] = [
    '*.log', '*.tmp', '*.bak', '*.swp', '*.swo', '*.cache', '*.DS_Store',
    '*.pyc', '*.pyo', '*.exe', '*.dll', '*.o', '*.so', '*.bin',
    '*.zip', '*.tar.gz', '*.rar', '*.7z', '*.gz', '*.bz2', '*.xz',
    '*.dmg', '*.iso',
    '*.class', '*.jar', '*.war', '*.ear',
    '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx',
    '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.svg', '*.ico',
    '*.mp3', '*.wav', '*.ogg', '*.mp4', '*.avi', '*.mkv',
    '*.lock',
]

# --- Icon Mapping ---
ICON_MAP: Dict[str, str] = {
    # Directories
    'dir': '📁',
    # Programming Languages & Scripts
    'py': '🐍', 'js': '📜', 'ts': '📜', 'jsx': '⚛️', 'tsx': '⚛️', 'html': '🌐',
    'css': '🎨', 'scss': '🎨', 'less': '🎨', 'c': '📄', 'cpp': '📄', 'h': '📄',
    'hpp': '📄', 'java': '☕', 'go': '🐿️', 'rs': '🦀', 'kt': '📄', 'php': '🐘',
    'rb': '💎', 'swift': '🐦', 'scala': '📄', 'cs': '📄', 'vb': '📄', 'lua': '🌙',
    'r': '📊', 'sh': '⚙️', 'bash': '⚙️', 'ps1': '⚙️', 'psm1': '⚙️', 'pl': '⚙️',
    'pm': '⚙️', 'tcl': '⚙️', 'pro': '⚙️', 'cmake': '⚙️', 'gradle': '🐘', 'kts': '⚙️',
    'groovy': '📄', 'dart': '🎯', 'fs': '📄', 'jl': '📄', 'vhd': '⚙️', 'sv': '⚙️', 'v': '⚙️',
    # Data & Config Files
    'json': '📄', 'xml': '📄', 'yaml': '📄', 'yml': '📄', 'md': '📝', 'txt': '📄',
    'csv': '📊', 'sql': '🗄️', 'ini': '⚙️', 'cfg': '⚙️', 'conf': '⚙️',
    'properties': '📄', 'toml': '📄', 'env': '⚙️', 'rc': '⚙️',
    # Common Files (by name, handled by get_file_extension)
    'readme': '📖', 'license': '⚖️', 'gitignore': '🚫', 'editorconfig': '⚙️',
    'dockerfile': '🐳', 'makefile': '⚙️', 'jenkinsfile': '⚙️', 'vagrantfile': '⚙️',
    'gemfile': '💎', 'procfile': '⚙️', 'ipynb': '📊',
    # Other / Fallback
    'text': '📄', 'error': '⚠️', 'default': '📄',
}


# --- Stylesheet ---
# Using f-string for stylesheet to embed color variables
GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
}}
QMainWindow {{ background-color: {COLORS['background']}; }}
QLabel {{ color: {COLORS['textSecondary']}; padding: 2px; }}
QLineEdit, QTextEdit {{
    background-color: {COLORS['cardBackground']};
    color: {COLORS['textPrimary']};
    border: 1px solid {COLORS['borderDark']};
    border-radius: 3px; padding: 6px;
    selection-background-color: {COLORS['primaryBlue']};
    selection-color: {COLORS['textPrimary']};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLORS['lightBlue']};
    background-color: {COLORS['focusBackground']};
}}
QLineEdit[readOnly="true"] {{
    background-color: {COLORS['cardBackground']};
    color: {COLORS['textSecondary']};
    border: 1px solid {COLORS['borderLight']};
}}
QTextEdit {{ font-family: "Consolas", "Monaco", "DejaVu Sans Mono", "Courier New", monospace; }}
QPushButton {{
    background-color: {COLORS['buttonNormalBg']};
    color: {COLORS['textPrimary']};
    border: 1px solid {COLORS['buttonBorder']};
    padding: 7px 12px; border-radius: 3px; min-height: 20px;
}}
QPushButton:hover {{
    background-color: {COLORS['buttonHoverBg']};
    border-color: {COLORS['buttonHoverBorder']};
}}
QPushButton:pressed {{ background-color: {COLORS['buttonPressedBg']}; }}
QPushButton:disabled {{
    background-color: {COLORS['disabledBg']};
    color: {COLORS['disabledText']};
    border-color: {COLORS['disabledBorder']};
}}
QPushButton#generateButton {{
    background-color: {COLORS['primaryBlue']};
    color: {COLORS['textPrimary']};
    font-weight: bold; border: 1px solid {COLORS['generateButtonDarkBlue']};
    padding: 8px 15px;
}}
QPushButton#generateButton:hover {{ background-color: {COLORS['lightBlue']}; }}
QPushButton#generateButton:pressed {{ background-color: {COLORS['generateButtonDarkBlue']}; }}

/* Unified style for clear buttons */
QPushButton[class="clearButton"] {{
    font-size: 9pt; font-weight: bold; color: {COLORS['primaryRed']};
    background-color: {COLORS['clearButtonBg']};
    border: 1px solid {COLORS['clearButtonRedBorder']};
    padding: 1px;
    min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px;
    border-radius: 13px;
}}
QPushButton[class="clearButton"]:hover {{
    background-color: {COLORS['clearButtonHoverBg']};
    color: {COLORS['clearButtonHoverText']};
}}
QPushButton[class="clearButton"]:pressed {{
    background-color: {COLORS['clearButtonPressedBg']};
}}

QTreeView {{
    background-color: {COLORS['cardBackground']};
    color: {COLORS['textPrimary']};
    border: 1px solid {COLORS['borderDark']};
    border-radius: 3px; alternate-background-color: {COLORS['treeViewAlternateBg']};
    padding: 2px; show-decoration-selected: 1;
}}
QTreeView::item {{ padding: 5px; border-radius: 2px; }}
QTreeView::item:hover {{
    background-color: {COLORS['buttonNormalBg']};
    color: {COLORS['textPrimary']};
}}
QTreeView::item:selected {{
    background-color: {COLORS['primaryBlue']};
    color: {COLORS['textPrimary']};
}}
QTreeView::item:selected:active {{ background-color: {COLORS['primaryBlue']}; }}
QTreeView::item:selected:!active {{ background-color: {COLORS['generateButtonDarkBlue']}; }}
QTreeView::branch {{ background: transparent; }}
QGroupBox {{
    background-color: {COLORS['groupBoxBackground']};
    border: 1px solid {COLORS['borderDark']};
    border-radius: 4px;
    margin-top: 10px; padding: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 2px 8px; margin-left: 10px; color: {COLORS['lightBlue']};
    font-weight: bold;
    background-color: {COLORS['cardBackground']};
    border-radius: 3px;
}}
QScrollBar:vertical {{
    border: none; background: {COLORS['background']};
    width: 12px; margin: 0px 0px 0px 2px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['scrollHandleNormal']};
    min-height: 25px; border-radius: 5px; border: 1px solid {COLORS['scrollHandleBorder']};
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['lightBlue']};
    border-color: {COLORS['lightBlue']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ background: none; border: none; height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QScrollBar:horizontal {{
    border: none; background: {COLORS['background']};
    height: 12px; margin: 2px 0px 0px 0px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['scrollHandleNormal']};
    min-width: 25px; border-radius: 5px; border: 1px solid {COLORS['scrollHandleBorder']};
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['lightBlue']};
    border-color: {COLORS['lightBlue']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ background: none; border: none; width: 0px; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
QDialog {{ background-color: {COLORS['background']}; }}
QMessageBox {{ background-color: {COLORS['cardBackground']}; }}
QMessageBox QLabel {{ color: {COLORS['textPrimary']}; }}
"""

# --- Helper Functions ---

def get_file_extension(filepath: str) -> str:
    name = os.path.basename(filepath)
    parts = name.split('.')
    if len(parts) > 1 and parts[-1]: return parts[-1].lower()
    common_names_without_ext = {
        'dockerfile', 'makefile', 'readme', 'license', '.gitattributes',
        '.editorconfig', 'jenkinsfile', 'vagrantfile', 'gemfile', 'procfile',
        '.gitignore', '.env'
    }
    name_lower = name.lower()
    if name_lower in common_names_without_ext: return name_lower
    if name.startswith('.') and len(parts) == 1:
        return name_lower[1:]
    if name.startswith('.') and len(parts) > 1 and not parts[-1]:
         return parts[1].lower() if len(parts) > 1 else 'text'
    return 'text'

def is_excluded(name: str, is_dir: bool) -> bool:
     name_lower = name.lower()
     if is_dir:
         # Exclude dot-directories like .git, .idea, etc., but allow specific ones like .well-known
         return name_lower in EXCLUDE_DIRS or (name.startswith('.') and name_lower not in {'.well-known'})
     else:
         # Exclude specific files and patterns, but allow some common dotfiles (like .env, .bashrc)
         if name_lower in EXCLUDE_FILES_EXACT:
             return True
         # Allow .env, .<anything>rc files, and other dotfiles not in EXCLUDE_FILES_EXACT
         if name.startswith('.') and name_lower not in EXCLUDE_FILES_EXACT and \
            not name_lower.startswith(".git") and \
            not name_lower == ".env" and \
            not name_lower.endswith("rc"):
            return True # Exclude if it's a dotfile not explicitly allowed/common

         for pattern in EXCLUDE_FILES_PATTERNS:
             if fnmatch.fnmatch(name_lower, pattern): return True
         return False

def list_project_items(project_path: str) -> Tuple[List[Dict[str, Any]], str]:
    if not project_path or not os.path.isdir(project_path):
        return [], "Error: Project path is invalid or not a directory."

    items: List[Dict[str, Any]] = []
    project_path_abs = os.path.abspath(project_path)

    items.append({
        'Select': True, 'Type': '📁 Dir', 'Path': "", 'Depth': 0,
        'Name': os.path.basename(project_path_abs) or project_path_abs, 'IsDir': True
    })

    try:
        for root, dirs, files in os.walk(project_path_abs, topdown=True):
            current_relative_root = os.path.relpath(root, project_path_abs)
            if current_relative_root == ".": current_relative_root = ""
            current_dir_depth = current_relative_root.count(os.sep) if current_relative_root else 0

            valid_dirs = [d for d in dirs if not is_excluded(d, is_dir=True)]
            dirs[:] = valid_dirs

            for dir_name in sorted(valid_dirs):
                 dir_path_rel = os.path.join(current_relative_root, dir_name).replace("\\", "/")
                 items.append({
                     'Select': True, 'Type': '📁 Dir', 'Path': dir_path_rel,
                     'Depth': current_dir_depth + 1, 'Name': dir_name, 'IsDir': True
                 })

            valid_files = [f for f in files if not is_excluded(f, is_dir=False)]
            for file_name in sorted(valid_files):
                 file_path_rel = os.path.join(current_relative_root, file_name).replace("\\", "/")
                 items.append({
                     'Select': True, 'Type': '📄 File', 'Path': file_path_rel,
                     'Depth': current_dir_depth + 1, 'Name': file_name, 'IsDir': False
                 })
    except PermissionError as e:
        error_path_rel = os.path.relpath(str(e.filename), project_path_abs) if e.filename else "Unknown Path"
        error_path_rel = error_path_rel.replace("\\", "/")
        items.append({
            'Select': False, 'Type': '⚠️ Error Dir', 'Path': error_path_rel,
            'Depth': error_path_rel.count(os.sep) if error_path_rel and error_path_rel != "." else 0,
            'Name': os.path.basename(str(e.filename) or "Access Denied"),
            'IsDir': True, 'Error': str(e)
        })
        print(f"Warning: Permission denied accessing '{e.filename}'. Added as error item.")
    except Exception as e:
        return items, f"An unexpected error occurred while scanning: {type(e).__name__}: {e}"

    if len(items) <= 1:
         try: has_any_entries = any(True for _ in os.scandir(project_path_abs))
         except Exception: has_any_entries = False
         if has_any_entries:
              return items, "No displayable files or sub-directories found (all might be excluded or filtered)."
         else:
              return items, "Project directory appears to be empty or inaccessible."
    return items, f"Found {len(items) - 1} items (excluding root). Scan complete."

def generate_text_from_selected_files(project_path: str, selected_items_data: List[Dict[str, Any]], custom_filename_base: Optional[str] = None) -> Tuple[Optional[str], str, int, int]:
    if not project_path or not os.path.isdir(project_path):
        return None, "Error: Project path is invalid.", 0, 0
    if not selected_items_data: return None, "Error: No file data provided for generation.", 0, 0

    files_to_read_items = [
        item for item in selected_items_data
        if item.get('Select', False) and not item.get('IsDir', True) and item.get('Type') != '⚠️ Error Dir'
    ]
    if not files_to_read_items: return None, "No files selected to generate context.", 0, 0
    files_to_read_items.sort(key=lambda x: x.get('Path', ''))

    content_parts: List[str] = []
    MAX_FILE_SIZE_READ = 1024 * 1024 # 1MB

    for item in files_to_read_items:
        relative_filepath = item['Path']
        full_filepath = os.path.join(project_path, relative_filepath)
        try:
            if not os.path.isfile(full_filepath):
                 content_parts.append(f"--- File: {relative_filepath} ---\nError: Path not found or is not a file.\n--- END OF FILE: {relative_filepath} ---\n")
                 continue
            file_size = os.path.getsize(full_filepath)
            if file_size == 0:
                 content_parts.append(f"--- File: {relative_filepath} ---\n(File is empty)\n--- END OF FILE: {relative_filepath} ---\n")
                 continue
            if file_size > MAX_FILE_SIZE_READ:
                 content_parts.append(f"--- File: {relative_filepath} ---\nNote: Skipped file larger than {MAX_FILE_SIZE_READ // 1024}KB.\n--- END OF FILE: {relative_filepath} ---\n")
                 continue
            try:
                with open(full_filepath, 'r', encoding='utf-8') as f: file_content = f.read()
                if '\0' in file_content:
                    content_parts.append(f"--- File: {relative_filepath} ---\nNote: Skipped potential binary file (contained NUL bytes).\n--- END OF FILE: {relative_filepath} ---\n")
                    continue
            except UnicodeDecodeError:
                 try:
                     with open(full_filepath, 'r', encoding='latin-1') as f: file_content = f.read()
                     if '\0' in file_content:
                          content_parts.append(f"--- File: {relative_filepath} ---\nNote: Skipped potential binary file (NUL bytes after latin-1).\n--- END OF FILE: {relative_filepath} ---\n")
                          continue
                     content_parts.append(f"--- File: {relative_filepath} (Latin-1 encoding) ---\n```\n{file_content.strip()}\n```\n--- END OF FILE: {relative_filepath} ---\n")
                     continue
                 except Exception:
                    content_parts.append(f"--- File: {relative_filepath} ---\nError: Could not decode file (binary or unknown encoding).\n--- END OF FILE: {relative_filepath} ---\n")
                    continue
            except Exception as e:
                 content_parts.append(f"--- File: {relative_filepath} ---\nError reading file content: {type(e).__name__}: {e}\n--- END OF FILE: {relative_filepath} ---\n")
                 continue
            lang_hint = get_file_extension(relative_filepath)
            content_parts.append(f"--- File: {relative_filepath} ---\n```{lang_hint}\n{file_content.strip()}\n```\n--- END OF FILE: {relative_filepath} ---\n")
        except Exception as e:
            content_parts.append(f"--- File: {relative_filepath} ---\nUnexpected error processing file: {type(e).__name__}: {e}\n--- END OF FILE: {relative_filepath} ---\n")

    if not content_parts: return None, "No content generated. Files might have issues or were skipped.", 0, 0
    
    # Construct the header
    project_name = os.path.basename(project_path)
    header = f"--- START OF PROJECT CONTEXT FOR: {project_name} ---\n"
    header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"Number of files included: {len(files_to_read_items)}\n"
    header += "---\n\n"
    
    final_text = header + "\n".join(content_parts)
    final_text += f"\n--- END OF PROJECT CONTEXT FOR: {project_name} ---"


    word_count = len(final_text.split())
    token_count_approx = int(len(final_text) / 4) # General LLM token approximation

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if custom_filename_base and custom_filename_base.strip():
        # Sanitize filename: replace non-alphanumeric, non-space, non-underscore, non-hyphen with nothing, then replace spaces with underscores.
        sanitized_base = re.sub(r'[^\w\s-]', '', custom_filename_base).strip().replace(" ", "_")
        if not sanitized_base: # Fallback if sanitized base is empty
            sanitized_base = "project_context"
        output_filename = f"{sanitized_base}_{timestamp}.txt"
    else:
        # Default filename based on project name, sanitize spaces
        default_base = re.sub(r'[^\w\s-]', '', project_name).strip().replace(" ", "_")
        if not default_base: default_base = "project_context"
        output_filename = f"{default_base}_{timestamp}.txt"


    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f: f.write(final_text)
        return output_filepath, f"Context file generated: {output_filename} ({len(files_to_read_items)} files processed)", word_count, token_count_approx
    except Exception as e:
        return None, f"Error saving output file '{output_filename}': {e}", 0, 0

# --- Helper Dialog for viewing file content ---
class ViewFileDialog(QDialog):
    def __init__(self, file_path: str, content: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"View File: {os.path.basename(file_path)}")
        self.setMinimumSize(600, 400)
        self.setGeometry(150, 150, 900, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        font = QFont("Consolas", 10); font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)
        button_box_layout = QHBoxLayout(); button_box_layout.setContentsMargins(0, 5, 0, 0); button_box_layout.addStretch()
        close_button = QPushButton("Close"); close_button.clicked.connect(self.accept)
        button_box_layout.addWidget(close_button); button_box_layout.addStretch()
        layout.addLayout(button_box_layout)
        self.setLayout(layout)

# --- PyQt6 GUI Application ---
class ProjectContextGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Context Generator v1.3 :: Futura Edition") 
        self.setGeometry(100, 100, 1100, 850)
        self.setMinimumSize(QSize(800, 600))
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self._pinned_paths: List[Optional[str]] = [None] * MAX_PINNED_DIRS
        self._recent_paths: List[str] = []
        self.load_settings()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget) # Store main_layout for stretch manipulation
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # --- Top Panel: Navigation & Project Group ---
        self.top_group_box = QGroupBox("Navigation & Project")
        top_panel_layout = QVBoxLayout(self.top_group_box)
        top_panel_layout.setContentsMargins(10, 20, 10, 10)
        top_panel_layout.setSpacing(8)

        self.setup_shortcuts_ui(top_panel_layout)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(6)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Enter project path or browse...")
        browse_button = QPushButton("Browse...")
        load_button = QPushButton("Load Project")
        path_layout.addWidget(QLabel("Project Path:"))
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(browse_button)
        path_layout.addWidget(load_button)
        top_panel_layout.addLayout(path_layout)
        self.main_layout.addWidget(self.top_group_box, 1) # Stretch factor 1

        self.status_output = QLabel("Status: Ready. Select or enter a project path.")
        self.status_output.setStyleSheet(f"padding: 3px; color: {COLORS['lightBlue']};")
        self.main_layout.addWidget(self.status_output, 0) # Stretch factor 0 (fixed height)

        # --- Middle Section: File Tree View Group ---
        self.tree_group_box = QGroupBox("Project Files & Folders (Check to include)")
        tree_and_selection_layout = QVBoxLayout(self.tree_group_box)
        tree_and_selection_layout.setContentsMargins(10, 20, 10, 10)
        tree_and_selection_layout.setSpacing(6)
        
        self.tree_model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree_and_selection_layout.addWidget(self.tree_view, 1) 

        selection_button_layout = QHBoxLayout()
        selection_button_layout.setSpacing(6)
        self.select_all_button = QPushButton("Select All")
        self.deselect_all_button = QPushButton("Deselect All")
        self.copy_names_button = QPushButton("Copy File Name") 
        self.copy_names_button.setEnabled(False) 
        self.toggle_fullscreen_button = QPushButton("Toggle Fullscreen Tree") # New button
        self._is_tree_fullscreen = False # State variable for fullscreen toggle

        selection_button_layout.addWidget(self.select_all_button)
        selection_button_layout.addWidget(self.deselect_all_button)
        selection_button_layout.addStretch(1) 
        selection_button_layout.addWidget(self.copy_names_button) 
        selection_button_layout.addWidget(self.toggle_fullscreen_button) # Add toggle button
        tree_and_selection_layout.addLayout(selection_button_layout)
        self.main_layout.addWidget(self.tree_group_box, 6) # Stretch factor 6 (approx 75%)

        # --- Bottom Section: Output Generation Group ---
        self.output_group_box = QGroupBox("Generate & Output") 
        output_group_layout = QVBoxLayout(self.output_group_box)
        output_group_layout.setContentsMargins(10, 20, 10, 10) 
        output_group_layout.setSpacing(8)

        filename_input_layout = QHBoxLayout()
        filename_input_layout.addWidget(QLabel("Output Filename Base:"))
        self.output_filename_input = QLineEdit()
        self.output_filename_input.setPlaceholderText("e.g., my_project_context (optional)")
        filename_input_layout.addWidget(self.output_filename_input, 1)
        output_group_layout.addLayout(filename_input_layout)

        self.generate_button = QPushButton("Generate Context File")
        self.generate_button.setObjectName("generateButton")
        output_group_layout.addWidget(self.generate_button)

        output_actions_layout = QHBoxLayout()
        output_actions_layout.setSpacing(6)
        self.output_file_label = QLabel("Last Output:")
        self.output_file_path_display = QLineEdit()
        self.output_file_path_display.setReadOnly(True)
        self.output_file_path_display.setPlaceholderText("Generated file path will appear here")
        self.open_output_folder_button = QPushButton("Open Output Dir")
        self.view_generated_file_button = QPushButton("View File")
        self.view_generated_file_button.setEnabled(False)
        output_actions_layout.addWidget(self.output_file_label)
        output_actions_layout.addWidget(self.output_file_path_display, 1)
        output_actions_layout.addWidget(self.open_output_folder_button)
        output_actions_layout.addWidget(self.view_generated_file_button)
        output_group_layout.addLayout(output_actions_layout)

        output_group_layout.addWidget(QLabel("Log:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(100)
        self.log_output.setStyleSheet(f"color: {COLORS['textSecondary']}; font-size: 9pt;")
        output_group_layout.addWidget(self.log_output)
        self.main_layout.addWidget(self.output_group_box, 1) 

        # --- Connections ---
        browse_button.clicked.connect(self.browse_directory)
        load_button.clicked.connect(self.load_project_files)
        self.tree_model.itemChanged.connect(self.handle_item_changed)
        self.select_all_button.clicked.connect(lambda: self.update_all_selections(True))
        self.deselect_all_button.clicked.connect(lambda: self.update_all_selections(False))
        self.copy_names_button.clicked.connect(self.copy_selected_file_names) 
        self.tree_view.selectionModel().selectionChanged.connect(self.update_copy_button_state)
        self.toggle_fullscreen_button.clicked.connect(self.toggle_tree_fullscreen) # Connect new button
        
        self.generate_button.clicked.connect(self.generate_context_file)
        self.open_output_folder_button.clicked.connect(self.open_output_folder)
        self.view_generated_file_button.clicked.connect(self.view_generated_file)
        self.tree_view.doubleClicked.connect(self.handle_tree_double_click)

        self._project_path: str = ""
        self._all_items_data: List[Dict[str, Any]] = []
        self._in_item_change_handler = False
        self._current_generated_filepath: Optional[str] = None
        self.update_pinned_buttons_ui()
        self.update_recent_buttons_ui()

    def setup_shortcuts_ui(self, parent_layout: QVBoxLayout):
        shortcuts_container_layout = QHBoxLayout(); shortcuts_container_layout.setSpacing(10)
        
        pinned_group = QGroupBox("Pinned Directories"); 
        pinned_group_layout = QVBoxLayout(); pinned_group_layout.setSpacing(5)
        pinned_group.setLayout(pinned_group_layout)
        self.pinned_buttons: List[QPushButton] = []
        self.clear_pinned_buttons: List[QPushButton] = []

        for i in range(MAX_PINNED_DIRS):
            row_layout = QHBoxLayout(); row_layout.setSpacing(3)
            pin_button = QPushButton(f"Pin Slot {i+1}")
            pin_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            pin_button.clicked.connect(partial(self.pinned_button_action, i))
            self.pinned_buttons.append(pin_button); row_layout.addWidget(pin_button, 1)
            clear_button = QPushButton("X"); clear_button.setProperty("class", "clearButton")
            clear_button.setToolTip(f"Clear pin from slot {i+1}")
            clear_button.clicked.connect(partial(self.clear_pinned_directory, i))
            self.clear_pinned_buttons.append(clear_button); row_layout.addWidget(clear_button)
            pinned_group_layout.addLayout(row_layout)
        shortcuts_container_layout.addWidget(pinned_group, 1)

        recent_group = QGroupBox("Recent Directories"); 
        recent_group_layout = QVBoxLayout(); recent_group_layout.setSpacing(5)
        recent_group.setLayout(recent_group_layout)
        self.recent_buttons: List[QPushButton] = []
        self.clear_recent_buttons: List[QPushButton] = [] 

        for i in range(MAX_RECENT_DIRS):
            row_layout = QHBoxLayout(); row_layout.setSpacing(3)
            recent_button = QPushButton(f"Recent {i+1}")
            recent_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            recent_button.setVisible(False)
            recent_button.clicked.connect(partial(self.load_recent_directory_action, i))
            self.recent_buttons.append(recent_button); row_layout.addWidget(recent_button, 1)

            clear_recent_btn = QPushButton("X"); clear_recent_btn.setProperty("class", "clearButton")
            clear_recent_btn.setToolTip(f"Clear recent directory from slot {i+1}")
            clear_recent_btn.setVisible(False) 
            clear_recent_btn.clicked.connect(partial(self.clear_recent_directory, i))
            self.clear_recent_buttons.append(clear_recent_btn); row_layout.addWidget(clear_recent_btn)
            recent_group_layout.addLayout(row_layout)
            
        recent_group_layout.addStretch(1)
        shortcuts_container_layout.addWidget(recent_group, 1)
        
        parent_layout.addLayout(shortcuts_container_layout)

    def load_settings(self):
        pinned_values = self.settings.value(SETTINGS_PINNED_DIRS, [])
        if isinstance(pinned_values, list):
            self._pinned_paths = [path if isinstance(path, str) else None for path in pinned_values[:MAX_PINNED_DIRS]]
            while len(self._pinned_paths) < MAX_PINNED_DIRS: self._pinned_paths.append(None)
        else: self._pinned_paths = [None] * MAX_PINNED_DIRS
        recent_values = self.settings.value(SETTINGS_RECENT_DIRS, [])
        if isinstance(recent_values, list):
            # Filter out invalid paths and duplicates when loading
            unique_valid_paths = []
            for path in (p for p in recent_values if isinstance(p, str) and os.path.isdir(p)):
                if path not in unique_valid_paths:
                    unique_valid_paths.append(path)
            self._recent_paths = unique_valid_paths
        else: self._recent_paths = []

    def save_settings(self):
        self.settings.setValue(SETTINGS_PINNED_DIRS, [path for path in self._pinned_paths if path is not None])
        self.settings.setValue(SETTINGS_RECENT_DIRS, self._recent_paths[:MAX_RECENT_DIRS])

    def closeEvent(self, event): self.save_settings(); super().closeEvent(event)

    def update_pinned_buttons_ui(self):
        for i in range(MAX_PINNED_DIRS):
            path = self._pinned_paths[i]
            if path and os.path.isdir(path):
                display_name = os.path.basename(path) or path
                self.pinned_buttons[i].setText(display_name)
                self.pinned_buttons[i].setToolTip(f"Load: {path}")
                if i < len(self.clear_pinned_buttons): self.clear_pinned_buttons[i].setEnabled(True)
            else:
                self.pinned_buttons[i].setText(f"Pin Slot {i+1} (Empty)")
                self.pinned_buttons[i].setToolTip("Click to pin current project path to this slot.")
                if i < len(self.clear_pinned_buttons): self.clear_pinned_buttons[i].setEnabled(False)
                self._pinned_paths[i] = None # Ensure it's None if path is invalid

    def pinned_button_action(self, index: int):
        current_project_path = self.path_input.text().strip()
        if index < len(self._pinned_paths) and self._pinned_paths[index] and os.path.isdir(self._pinned_paths[index]):
            self.path_input.setText(self._pinned_paths[index]); self.load_project_files()
        elif current_project_path and os.path.isdir(current_project_path):
            self.pin_directory(index, current_project_path)
        elif not current_project_path: self.status_output.setText("Status: Enter or browse to a project path to pin it.")
        else: self.status_output.setText(f"Status: Path '{current_project_path}' is not a valid directory to pin.")

    def pin_directory(self, index: int, path: str):
        if not os.path.isdir(path):
            self.status_output.setText(f"Status: Cannot pin '{path}', it's not a valid directory."); return
        path_abs = os.path.abspath(path)
        try:
            other_idx = self._pinned_paths.index(path_abs)
            if other_idx != index: self._pinned_paths[other_idx] = None
        except ValueError: pass
        
        if path_abs in self._recent_paths:
            self._recent_paths.remove(path_abs)
        
        self._pinned_paths[index] = path_abs
        self.status_output.setText(f"Status: Pinned '{os.path.basename(path_abs) or path_abs}' to slot {index+1}.")
        self.update_pinned_buttons_ui()
        self.update_recent_buttons_ui()
        self.save_settings()

    def clear_pinned_directory(self, index: int):
        if index < len(self._pinned_paths) and self._pinned_paths[index]:
            cleared_path = self._pinned_paths[index]
            cleared_path_name = os.path.basename(cleared_path) or cleared_path
            self._pinned_paths[index] = None
            self.status_output.setText(f"Status: Cleared pin from slot {index+1} ('{cleared_path_name}').")
            self.update_pinned_buttons_ui(); self.save_settings()

    def update_recent_buttons_ui(self):
        valid_recent_paths = []
        for path in self._recent_paths:
            if path and os.path.isdir(path) and path not in self._pinned_paths and path not in valid_recent_paths:
                valid_recent_paths.append(path)
        self._recent_paths = valid_recent_paths[:MAX_RECENT_DIRS]

        for i in range(MAX_RECENT_DIRS):
            clear_btn = self.clear_recent_buttons[i]
            recent_btn = self.recent_buttons[i]
            if i < len(self._recent_paths):
                path = self._recent_paths[i]; display_name = os.path.basename(path) or path
                recent_btn.setText(display_name); recent_btn.setToolTip(f"Load: {path}")
                recent_btn.setVisible(True)
                clear_btn.setVisible(True); clear_btn.setEnabled(True)
            else: 
                recent_btn.setVisible(False)
                clear_btn.setVisible(False); clear_btn.setEnabled(False)
                recent_btn.setText(f"Recent {i+1}") 
                recent_btn.setToolTip("")


    def add_to_recent_directories(self, path: str):
        if not path or not os.path.isdir(path): return
        path_abs = os.path.abspath(path)
        if path_abs in self._pinned_paths:
            self.update_recent_buttons_ui()
            return 
        if path_abs in self._recent_paths: self._recent_paths.remove(path_abs)
        self._recent_paths.insert(0, path_abs)
        self._recent_paths = self._recent_paths[:MAX_RECENT_DIRS]
        self.update_recent_buttons_ui(); self.save_settings()

    def load_recent_directory_action(self, index: int):
        if index < len(self._recent_paths):
            path = self._recent_paths[index]
            if os.path.isdir(path):
                self.path_input.setText(path); self.load_project_files()
            else:
                QMessageBox.warning(self, "Recent Path Error", f"The recent path '{path}' is no longer valid or accessible. It will be removed from recent list.")
                self._recent_paths.pop(index)
                self.update_recent_buttons_ui()
                self.save_settings()


    def clear_recent_directory(self, index: int):
        if index < len(self._recent_paths):
            cleared_path = self._recent_paths.pop(index)
            cleared_path_name = os.path.basename(cleared_path) or cleared_path
            self.status_output.setText(f"Status: Cleared recent directory '{cleared_path_name}'.")
            self.update_recent_buttons_ui()
            self.save_settings()


    def browse_directory(self):
        current_path_from_input = self.path_input.text().strip(); start_location = QDir.homePath()
        if current_path_from_input:
            if os.path.isdir(current_path_from_input): start_location = os.path.abspath(current_path_from_input)
            else:
                parent_dir = os.path.dirname(current_path_from_input)
                if parent_dir and os.path.isdir(parent_dir): start_location = os.path.abspath(parent_dir)
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory", start_location)
        if directory: self.path_input.setText(directory); self.load_project_files()

    def load_project_files(self):
        project_path = self.path_input.text().strip()
        if not project_path:
            self.status_output.setText("Status: Please enter or browse to a project path.")
            self.tree_model.clear(); self._all_items_data = []; self._project_path = ""
            self._current_generated_filepath = None; self.output_file_path_display.clear()
            self.view_generated_file_button.setEnabled(False); return

        project_path_abs = os.path.abspath(project_path)
        if not os.path.isdir(project_path_abs):
            self.status_output.setText(f"Status: Error - Path '{project_path}' is not a valid directory.")
            QMessageBox.warning(self, "Load Error", f"Path '{project_path}' is not a valid directory.")
            self.tree_model.clear(); self._all_items_data = []; self._project_path = ""
            self._current_generated_filepath = None; self.output_file_path_display.clear()
            self.view_generated_file_button.setEnabled(False); return

        self.status_output.setText(f"Status: Loading from {project_path_abs}..."); QApplication.processEvents()
        items_list, msg = list_project_items(project_path_abs)
        self._project_path = project_path_abs; self._all_items_data = items_list
        self._current_generated_filepath = None; self.add_to_recent_directories(project_path_abs)
        self.tree_model.clear(); self.output_file_path_display.clear(); self.view_generated_file_button.setEnabled(False)

        if len(items_list) <= 1 and items_list[0]['Path'] == "": 
             self.status_output.setText(f"Status: {msg}")
             if "Error:" in msg or "Could not" in msg or "denied" in msg : QMessageBox.warning(self, "Load Problem", msg)
             elif "No displayable" in msg or "empty" in msg or "filtered" in msg: QMessageBox.information(self, "Load Info", msg)
             return

        invisible_root_model_item = self.tree_model.invisibleRootItem()
        qt_items_map: Dict[str, QStandardItem] = {}
        children_by_parent: Dict[str, List[QStandardItem]] = {}
        self._in_item_change_handler = True

        for item_data in self._all_items_data:
            path = item_data.get('Path', ''); name = item_data.get('Name', 'Unknown')
            is_dir = item_data.get('IsDir', False)
            item_type = item_data.get('Type', '📄 File' if not is_dir else '📁 Dir')
            is_selected = item_data.get('Select', True); prefix = ""; display_text = name
            if is_dir:
                if item_type == '⚠️ Error Dir':
                    prefix = ICON_MAP.get('error', '⚠️')
                    display_text = f"{name} (Error: {item_data.get('Error', 'Access Denied')})"
                else: prefix = ICON_MAP.get('dir', '📁')
            else:
                extension_or_type = get_file_extension(path)
                prefix = ICON_MAP.get(extension_or_type, ICON_MAP.get('default', '📄'))
            qt_item = QStandardItem(f"{prefix} {display_text}"); qt_item.setEditable(False)
            qt_item.setData(item_data, Qt.ItemDataRole.UserRole)
            if item_type != '⚠️ Error Dir':
                qt_item.setFlags(qt_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                qt_item.setCheckState(Qt.CheckState.Checked if is_selected else Qt.CheckState.Unchecked)
            else: qt_item.setFlags(qt_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            qt_items_map[path] = qt_item
            if path == "": continue
            parent_path = os.path.dirname(path).replace("\\", "/")
            if parent_path not in children_by_parent: children_by_parent[parent_path] = []
            children_by_parent[parent_path].append(qt_item)

        def sort_key_dirs_first(item: QStandardItem):
            item_data = item.data(Qt.ItemDataRole.UserRole)
            is_dir = item_data.get('IsDir', False); name = item_data.get('Name', '')
            return (not is_dir, name.lower())

        root_path = ""; root_qt_item = qt_items_map.get(root_path)
        if root_qt_item:
            invisible_root_model_item.appendRow(root_qt_item)
            root_children_items = children_by_parent.get(root_path, [])
            sorted_root_children = sorted(root_children_items, key=sort_key_dirs_first)
            for child_qt_item in sorted_root_children: root_qt_item.appendRow(child_qt_item)
        else:
            print(f"Error: Project root item (path='') not found."); self.status_output.setText("Status: Error - Could not load project root.")
            self._in_item_change_handler = False; return

        sorted_parent_paths_for_processing = sorted(
            [p for p in children_by_parent.keys() if p != root_path],
            key=lambda p: (p.count(os.sep), p)
        )
        for parent_path in sorted_parent_paths_for_processing:
            parent_qt_item = qt_items_map.get(parent_path)
            if not parent_qt_item:
                print(f"Warning: Parent QStandardItem for path '{parent_path}' not found."); continue
            children_items = children_by_parent.get(parent_path, [])
            sorted_children = sorted(children_items, key=sort_key_dirs_first)
            for child_qt_item in sorted_children: parent_qt_item.appendRow(child_qt_item)

        self._in_item_change_handler = False; self.status_output.setText(f"Status: {msg}")
        if root_qt_item:
            self.tree_view.expand(root_qt_item.index())
            self.tree_view.resizeColumnToContents(0)
        self.update_copy_button_state() 

    def handle_item_changed(self, item: QStandardItem):
        if self._in_item_change_handler: return
        self._in_item_change_handler = True
        try:
            item_data = item.data(Qt.ItemDataRole.UserRole);
            if not item_data or not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                self._in_item_change_handler = False; return
            new_state = item.checkState() == Qt.CheckState.Checked; item_path = item_data.get('Path')
            if item_path is not None:
                 try:
                     found_data = next(d for d in self._all_items_data if d.get('Path') == item_path)
                     found_data['Select'] = new_state
                 except StopIteration: print(f"Warning: Could not find item path {item_path} in _all_items_data.")
            if item_data.get('IsDir', False) or item_path == "": self._propagate_selection_to_children(item, new_state)
        finally: self._in_item_change_handler = False

    def _propagate_selection_to_children(self, parent_qstandard_item: QStandardItem, select_value_for_children: bool):
        check_state_to_set = Qt.CheckState.Checked if select_value_for_children else Qt.CheckState.Unchecked
        for row in range(parent_qstandard_item.rowCount()):
            child_qstandard_item = parent_qstandard_item.child(row, 0)
            if child_qstandard_item:
                child_data = child_qstandard_item.data(Qt.ItemDataRole.UserRole)
                if child_data and child_data.get('Type') != '⚠️ Error Dir':
                    child_path = child_data.get('Path')
                    if child_path is not None:
                        try:
                            found_child_data_dict = next(
                                data_dict for data_dict in self._all_items_data
                                if data_dict.get('Path') == child_path
                            )
                            found_child_data_dict['Select'] = select_value_for_children
                        except StopIteration:
                            print(f"Warning: Could not find child item path {child_path} in _all_items_data during propagation.")
                if child_qstandard_item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    if child_qstandard_item.checkState() != check_state_to_set:
                        child_qstandard_item.setCheckState(check_state_to_set)
                if child_qstandard_item.hasChildren():
                    self._propagate_selection_to_children(child_qstandard_item, select_value_for_children)

    def update_all_selections(self, select_value: bool):
        if not self._all_items_data:
            self.status_output.setText("Status: No project items loaded.")
            return
        self._in_item_change_handler = True 
        check_state_to_set = Qt.CheckState.Checked if select_value else Qt.CheckState.Unchecked
        for item_data_dict in self._all_items_data:
            if item_data_dict.get('Type') != '⚠️ Error Dir':
                item_data_dict['Select'] = select_value
        def _recursive_set_check_state(parent_qstandard_item: QStandardItem):
            for row in range(parent_qstandard_item.rowCount()):
                child_qstandard_item = parent_qstandard_item.child(row, 0)
                if child_qstandard_item:
                    if child_qstandard_item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                        child_qstandard_item.setCheckState(check_state_to_set)
                    if child_qstandard_item.hasChildren():
                        _recursive_set_check_state(child_qstandard_item)
        invisible_root = self.tree_model.invisibleRootItem()
        _recursive_set_check_state(invisible_root)
        self._in_item_change_handler = False
        self.status_output.setText(f"Status: {'All checkable items selected' if select_value else 'All checkable items deselected'}.")

    def update_copy_button_state(self):
        selected_indexes = self.tree_view.selectionModel().selectedRows()
        self.copy_names_button.setEnabled(bool(selected_indexes))

    def copy_selected_file_names(self):
        selected_paths: List[str] = []
        selected_indexes = self.tree_view.selectionModel().selectedRows()
        for index in selected_indexes:
            item = self.tree_model.itemFromIndex(index)
            if item:
                item_data = item.data(Qt.ItemDataRole.UserRole)
                if item_data:
                    path_to_copy = item_data.get('Path', '')
                    if path_to_copy == "" and self._project_path: # Root project directory
                        selected_paths.append(os.path.basename(self._project_path) or item_data.get('Name', ''))
                    elif path_to_copy: # Other items with a path
                        selected_paths.append(path_to_copy)
                    elif not path_to_copy and not self._project_path: # Fallback for odd cases
                         selected_paths.append(item_data.get('Name', 'Unknown Item'))

        if not selected_paths:
            self.log_output.append("Info: No items selected to copy."); return
        clipboard_text = "\n".join(selected_paths)
        QApplication.clipboard().setText(clipboard_text)
        self.log_output.append(f"Copied {len(selected_paths)} item paths to clipboard.")
        self.status_output.setText(f"Status: Copied {len(selected_paths)} item paths to clipboard.")

    def toggle_tree_fullscreen(self):
        if not self.tree_group_box: return 

        if not self._is_tree_fullscreen: # Entering fullscreen mode
            self.top_group_box.setVisible(False)
            self.status_output.setVisible(False)
            self.output_group_box.setVisible(False)

            # Adjust stretch factors: tree_group_box takes all available space
            # Pass the widget/layout object directly
            self.main_layout.setStretchFactor(self.top_group_box, 0)
            self.main_layout.setStretchFactor(self.status_output, 0)
            self.main_layout.setStretchFactor(self.tree_group_box, 100) # Dominant stretch
            self.main_layout.setStretchFactor(self.output_group_box, 0)
            
            self.toggle_fullscreen_button.setText("Exit Fullscreen Tree")
            self._is_tree_fullscreen = True
            self.status_output.setText("Status: Fullscreen tree view enabled.")
        else: # Exiting fullscreen mode
            self.top_group_box.setVisible(True)
            self.status_output.setVisible(True)
            self.output_group_box.setVisible(True)

            # Restore original stretch factors
            # Pass the widget/layout object directly
            self.main_layout.setStretchFactor(self.top_group_box, 1)
            self.main_layout.setStretchFactor(self.status_output, 0)
            self.main_layout.setStretchFactor(self.tree_group_box, 6)
            self.main_layout.setStretchFactor(self.output_group_box, 1)

            self.toggle_fullscreen_button.setText("Toggle Fullscreen Tree")
            self._is_tree_fullscreen = False
            self.status_output.setText("Status: Fullscreen tree view disabled.")
        
        # It might be necessary to force the layout to update immediately
        self.main_layout.activate()

    def generate_context_file(self):
        if not self._project_path:
            self.log_output.append("Error: No project loaded."); QMessageBox.warning(self, "Generate Error", "No project loaded."); return
        selected_data = [item for item in self._all_items_data if item.get('Select', False)]
        if not any(not item.get('IsDir', True) for item in selected_data):
            self.log_output.append("Info: No files selected."); QMessageBox.information(self, "Generate Info", "No files selected."); return
        custom_filename_base = self.output_filename_input.text().strip()
        self.log_output.clear(); self.log_output.append("Generating context file..."); QApplication.processEvents()
        output_filepath_val, msg, word_count, token_count_approx = generate_text_from_selected_files(
            self._project_path, selected_data, custom_filename_base
        )
        self.log_output.append(msg)
        if output_filepath_val:
            self.output_file_path_display.setText(output_filepath_val)
            self._current_generated_filepath = output_filepath_val
            self.view_generated_file_button.setEnabled(True)
            self.log_output.append(f"Success: Output saved to {os.path.basename(output_filepath_val)}")
            self.log_output.append(f"Content stats: {word_count} words, ~{token_count_approx} tokens.")
            QMessageBox.information(self, "Generation Complete",
                                    f"Context file generated: {os.path.basename(output_filepath_val)}\n"
                                    f"Words: {word_count}, Tokens (approx): {token_count_approx}")
        else:
            self.output_file_path_display.clear(); self._current_generated_filepath = None
            self.view_generated_file_button.setEnabled(False)
            self.log_output.append("Generation failed or no content.")
            QMessageBox.warning(self, "Generation Failed", f"Could not generate context file.\nDetails: {msg}")

    def open_output_folder(self):
        output_dir_abs = os.path.abspath(OUTPUT_DIR); os.makedirs(output_dir_abs, exist_ok=True)
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir_abs)):
            QMessageBox.warning(self, "Open Folder Error", f"Could not open folder: {output_dir_abs}")
            self.log_output.append(f"Error: Could not open output folder '{output_dir_abs}'.")

    def view_generated_file(self):
        file_path_to_view = self._current_generated_filepath
        if not file_path_to_view or not os.path.isfile(file_path_to_view):
            QMessageBox.warning(self, "View File Error", "No valid output file or file does not exist.")
            self.log_output.append("Error: Cannot view file. Path invalid or file missing.")
            self.output_file_path_display.clear(); self._current_generated_filepath = None
            self.view_generated_file_button.setEnabled(False); return
        try:
            MAX_PREVIEW_SIZE = 2 * 1024 * 1024 # 2MB
            file_size = os.path.getsize(file_path_to_view)
            
            with open(file_path_to_view, 'r', encoding='utf-8', errors='replace') as f: 
                content = f.read(MAX_PREVIEW_SIZE)
            
            if file_size > MAX_PREVIEW_SIZE: 
                content += f"\n\n--- File truncated for viewing ({MAX_PREVIEW_SIZE//1024//1024}MB limit, total size: {file_size // 1024}KB) ---"
            
            if '\0' in content: # Check for NUL bytes after reading
               content = f"Note: This file appears to be binary or contains NUL bytes and might not display correctly.\nShowing partial content up to {MAX_PREVIEW_SIZE//1024//1024}MB.\n\n" + content.replace('\0', '[NUL]')


            dialog = ViewFileDialog(file_path_to_view, content, self); dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "View File Error", f"Could not read/display file: {type(e).__name__}: {e}")
            self.log_output.append(f"Error viewing file '{file_path_to_view}': {type(e).__name__}: {e}")

    def handle_tree_double_click(self, index: QModelIndex):
        item = self.tree_model.itemFromIndex(index);
        if not item: return
        item_data = item.data(Qt.ItemDataRole.UserRole);
        if not item_data: return
        is_dir = item_data.get('IsDir', False); item_path_rel = item_data.get('Path')
        if not is_dir:
             if self._project_path and item_path_rel is not None:
                full_file_path = os.path.join(self._project_path, item_path_rel)
                if os.path.isfile(full_file_path):
                    try:
                        MAX_PREVIEW_SIZE = 2 * 1024 * 1024 # 2MB
                        file_size = os.path.getsize(full_file_path)
                        
                        with open(full_file_path, 'r', encoding='utf-8', errors='replace') as f: 
                            content = f.read(MAX_PREVIEW_SIZE)
                        
                        if file_size > MAX_PREVIEW_SIZE: 
                            content += f"\n\n--- File truncated for viewing ({MAX_PREVIEW_SIZE//1024//1024}MB limit, total size: {file_size // 1024}KB) ---"
                        
                        if '\0' in content: # Check for NUL bytes after reading
                           content = f"Note: This file appears to be binary or contains NUL bytes and might not display correctly.\nShowing partial content up to {MAX_PREVIEW_SIZE//1024//1024}MB.\n\n" + content.replace('\0', '[NUL]')


                        dialog = ViewFileDialog(full_file_path, content, self); dialog.exec()
                    except UnicodeDecodeError:
                         QMessageBox.warning(self, "View File Error", f"Could not decode file '{os.path.basename(full_file_path)}' with UTF-8. It might be a binary file or use a different encoding.")
                         self.log_output.append(f"Error double-clicking file '{full_file_path}': UnicodeDecodeError")
                    except Exception as e:
                        QMessageBox.critical(self, "View File Error", f"Could not read file: {type(e).__name__}: {e}")
                        self.log_output.append(f"Error double-clicking file '{full_file_path}': {type(e).__name__}: {e}")
                else: self.log_output.append(f"Warning: File path does not exist: {full_file_path}")
             else: self.log_output.append("Warning: Cannot view file. Project path or item path invalid.")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    window = ProjectContextGenerator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()