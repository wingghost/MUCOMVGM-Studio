from __future__ import annotations

import json
import re
import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRect, QSize, QProcess, QDir, QUrl, QMimeData
from PySide6.QtGui import (
    QAction, QColor, QFont, QPainter, QTextCharFormat, QSyntaxHighlighter,
    QTextFormat, QKeySequence, QShortcut, QTextDocument, QTextCursor, QPainterPath,
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QDockWidget,
    QFileDialog, QFileSystemModel, QFormLayout, QFrame, QHBoxLayout, QTableView, QAbstractItemView, QMenu,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSpinBox, QStatusBar, QVBoxLayout, QWidget,
    QTabWidget, QColorDialog, QCheckBox, QGroupBox, QScrollArea, QTextEdit, QInputDialog,
)

from .config import APP_NAME, BASE_DIR, TEXT, THEMES, read_config, write_config
from .editor import MmlEditor
from .explorer import ExplorerFileSystemModel, ExplorerTable
from .player import PlayerMixin
from .settings_dialog import SettingsDialog

class MainWindow(PlayerMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.values = read_config()
        self.language = self.values["language"] if self.values["language"] in TEXT else "Japanese"
        self.values["language"] = self.language
        self.current_file: Path | None = None
        self.project_root = Path.cwd()
        self.process: QProcess | None = None
        self.player_compile_process: QProcess | None = None
        self.player_process: QProcess | None = None
        self._player_temp_files: set[Path] = set()
        self._player_temp_source: Path | None = None
        self._player_temp_vgm: Path | None = None
        self._build_ui()
        self.retranslate()
        self.apply_settings()
        self.new_file()
        saved_explorer = Path(self.values.get("explorer_path", str(Path.cwd())))
        initial_explorer = saved_explorer if saved_explorer.exists() and saved_explorer.is_dir() else Path.cwd()
        self.set_explorer_path(initial_explorer, add_history=True)
        self.resize(1200, 780)
        geometry = self.values.get("window_geometry", "")
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except (ValueError, TypeError):
                pass
        state = self.values.get("window_state", "")
        if state:
            try:
                self.restoreState(bytes.fromhex(state))
            except (ValueError, TypeError):
                pass
        for i, width in enumerate(self.values.get("explorer_column_widths", [])):
            if i < self.explorer_table.model().columnCount():
                self.explorer_table.setColumnWidth(i, width)
        order = Qt.SortOrder.DescendingOrder if self.values.get("explorer_sort_order") == "descending" else Qt.SortOrder.AscendingOrder
        self.explorer_table.sortByColumn(self.values.get("explorer_sort_column", 0), order)

    def tr(self, key):
        return TEXT.get(self.language, TEXT["Japanese"]).get(key, TEXT["Japanese"].get(key, key))

    def _build_ui(self):
        self.editor = MmlEditor(lambda: self.values)
        self.editor.document().modificationChanged.connect(self.update_title)
        self.editor.cursorPositionChanged.connect(self.update_cursor_status)
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("MainTabs")
        self.main_tabs.addTab(self.editor, "エディター")
        self.setCentralWidget(self.main_tabs)

        self.clipboard_paths = []
        self.clipboard_cut = False
        self.history = []
        self.history_index = -1
        self.file_model = ExplorerFileSystemModel(self)
        self.file_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)
        self.file_model.setReadOnly(False)
        self.explorer_panel = QWidget()
        explorer_layout = QVBoxLayout(self.explorer_panel)
        explorer_layout.setContentsMargins(4, 4, 4, 4)
        nav = QHBoxLayout()
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.up_button = QPushButton("↑")
        self.refresh_button = QPushButton("⟳")
        for button, slot in ((self.back_button, self.navigate_back), (self.forward_button, self.navigate_forward),
                             (self.up_button, self.navigate_up), (self.refresh_button, self.refresh_explorer)):
            button.setMaximumWidth(34)
            button.clicked.connect(slot)
            nav.addWidget(button)
        self.path_edit = QLineEdit(str(self.project_root))
        self.path_edit.returnPressed.connect(self.navigate_to_path)
        nav.addWidget(self.path_edit, 1)
        explorer_layout.addLayout(nav)
        self.explorer_table = ExplorerTable(self)
        self.explorer_table.setModel(self.file_model)
        self.explorer_table.setSortingEnabled(True)
        self.explorer_table.setAlternatingRowColors(False)
        self.explorer_table.verticalHeader().setVisible(False)
        self.explorer_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.explorer_table.horizontalHeader().setStretchLastSection(True)
        self.explorer_table.setColumnWidth(0, 190)
        self.explorer_table.setColumnWidth(1, 85)
        self.explorer_table.setColumnWidth(2, 100)
        self.explorer_table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        explorer_layout.addWidget(self.explorer_table, 1)
        self.file_model.setRootPath(str(self.project_root))
        self.explorer_table.setRootIndex(self.file_model.index(str(self.project_root)))
        self.explorer_dock = QDockWidget(self)
        self.explorer_dock.setWidget(self.explorer_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_dock)

        self.output_log = QPlainTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setFont(QFont("Consolas", 9))
        self.output_dock = QDockWidget(self)
        self.output_dock.setWidget(self.output_log)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)

        self.player_panel = QWidget()
        player_layout = QVBoxLayout(self.player_panel)
        player_layout.setContentsMargins(8, 8, 8, 8)
        player_buttons = QHBoxLayout()
        self.player_play_button = QPushButton("▶ 再生")
        self.player_stop_button = QPushButton("■ 停止")
        self.player_play_button.clicked.connect(self.play_current_mml)
        self.player_stop_button.clicked.connect(self.stop_player)
        player_buttons.addWidget(self.player_play_button)
        player_buttons.addWidget(self.player_stop_button)
        player_layout.addLayout(player_buttons)
        self.player_status_label = QLabel("停止中")
        self.player_status_label.setWordWrap(True)
        player_layout.addWidget(self.player_status_label)
        player_layout.addStretch(1)
        self.main_tabs.addTab(self.player_panel, "プレイヤー")
        # Keep the bottom-left corner occupied by the Explorer dock so it extends
        # to the bottom while Output spans only the editor side.
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setDockNestingEnabled(True)

        self.actions = {}
        self.action_settings = QAction(self)
        self.action_settings.triggered.connect(self.open_settings)

        self.status_label = QLabel()
        self.cursor_label = QLabel()
        status = QStatusBar()
        status.addWidget(self.status_label, 1)
        status.addPermanentWidget(self.cursor_label)
        self.setStatusBar(status)

        bar = self.menuBar()
        self.menu_file = bar.addMenu("")
        self.menu_edit = bar.addMenu("")
        self.menu_view = bar.addMenu("")
        self.menu_tools = bar.addMenu("")
        self.menu_help = bar.addMenu("")
        for key, callback, shortcut in (("new", self.new_file, "Ctrl+N"), ("open", self.open_file, "Ctrl+O"),
                                        ("save", self.save_file, "Ctrl+Shift+S"), ("save_compile", self.save_and_compile, "Ctrl+S"),
                                        ("compile", self.compile_file, "F5")):
            action = QAction(self)
            action.triggered.connect(callback)
            action.setShortcut(QKeySequence(shortcut))
            self.menu_file.addAction(action)
            self.actions[key] = action
        self.menu_file.addSeparator()
        self.action_save_as = QAction(self)
        self.action_save_as.triggered.connect(self.save_file_as)
        self.menu_file.addAction(self.action_save_as)
        self.action_open_folder = QAction(self)
        self.action_open_folder.triggered.connect(self.open_folder)
        self.menu_file.addAction(self.action_open_folder)
        self.action_exit = QAction(self)
        self.action_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.action_exit)
        edit_items = (("undo", self.editor.undo, "Ctrl+Z"), ("redo", self.editor.redo, "Ctrl+Y"),
                      ("cut", self.editor.cut, "Ctrl+X"), ("copy", self.editor.copy, "Ctrl+C"),
                      ("paste", self.editor.paste, "Ctrl+V"), ("select_all", self.editor.selectAll, "Ctrl+A"))
        for key, callback, shortcut in edit_items:
            action = QAction(self)
            action.triggered.connect(callback)
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            self.menu_edit.addAction(action)
            self.actions[key] = action
        self.menu_edit.addSeparator()
        self.action_find = QAction(self)
        self.action_find.setShortcut(QKeySequence.StandardKey.Find)
        self.action_find.triggered.connect(self.open_find)
        self.menu_edit.addAction(self.action_find)
        self.action_replace = QAction(self)
        self.action_replace.setShortcut(QKeySequence("Ctrl+R"))
        # ApplicationShortcut also works while a child dialog (e.g. Replace) is active.
        self.action_replace.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.action_replace.triggered.connect(self.open_replace)
        self.menu_edit.addAction(self.action_replace)
        self.menu_view.addAction(self.explorer_dock.toggleViewAction())
        self.menu_view.addAction(self.output_dock.toggleViewAction())
        self.menu_tools.addAction(self.action_settings)
        self.action_clear_output = QAction(self)
        self.action_clear_output.triggered.connect(self.output_log.clear)
        self.menu_tools.addAction(self.action_clear_output)
        self.action_about = QAction(self)
        self.action_about.triggered.connect(lambda: QMessageBox.about(self, self.tr("about_title"), self.tr("about")))
        self.menu_help.addAction(self.action_about)

        self.find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        self.find_next_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.find_next_shortcut.activated.connect(self._handle_f3)
        self.find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        self.find_prev_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.find_prev_shortcut.activated.connect(lambda: self.find_text(True))
        self.zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self.editor)
        self.zoom_in_shortcut.activated.connect(lambda: self.change_font_size(1))
        self.zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self.editor)
        self.zoom_out_shortcut.activated.connect(lambda: self.change_font_size(-1))

    def retranslate(self):
        self.setWindowTitle(APP_NAME)
        for menu, key in ((self.menu_file, "file"), (self.menu_edit, "edit"), (self.menu_view, "view"),
                          (self.menu_tools, "tools"), (self.menu_help, "help")):
            menu.setTitle(self.tr(key))
        for key, action in self.actions.items():
            action.setText(self.tr(key))
        self.action_save_as.setText(self.tr("save_as"))
        self.action_open_folder.setText(self.tr("open_folder"))
        self.action_exit.setText(self.tr("exit"))
        self.action_settings.setText(self.tr("settings"))
        self.action_clear_output.setText(self.tr("clear_output"))
        self.action_about.setText(self.tr("about_title"))
        self.action_find.setText(self.tr("find"))
        self.action_replace.setText(self.tr("replace"))
        self.back_button.setToolTip(self.tr("back"))
        self.forward_button.setToolTip(self.tr("forward"))
        self.up_button.setToolTip(self.tr("up"))
        self.refresh_button.setToolTip(self.tr("refresh"))
        self.explorer_dock.setWindowTitle(self.tr("explorer"))
        self.output_dock.setWindowTitle(self.tr("output"))
        self.main_tabs.setTabText(0, "エディター" if self.language == "Japanese" else "Editor")
        self.main_tabs.setTabText(1, "プレイヤー" if self.language == "Japanese" else "Player")
        self.player_play_button.setText("▶ 再生" if self.language == "Japanese" else "▶ Play")
        self.player_stop_button.setText("■ 停止" if self.language == "Japanese" else "■ Stop")
        self.player_status_label.setText("停止中" if self.language == "Japanese" else "Stopped")
        self.status_label.setText(self.tr("ready"))
        self.update_cursor_status()
        self.update_title()

    def apply_settings(self):
        theme = self.values["theme"]
        if theme in THEMES and theme != "System":
            self.values["colors"].update(THEMES[theme])
        elif theme == "System":
            palette = QApplication.palette()
            self.values["colors"]["editor_background"] = palette.color(palette.ColorRole.Base).name()
            self.values["colors"]["editor_foreground"] = palette.color(palette.ColorRole.Text).name()
        self.editor.apply_settings()
        write_config(self.values)

    def open_settings(self):
        dialog = SettingsDialog(self.values, self.language, self, on_apply=self.accept_settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept_settings(dialog.collect_values())

    def accept_settings(self, values):
        self.values = json.loads(json.dumps(values))
        self.language = self.values["language"] if self.values["language"] in TEXT else "Japanese"
        self.values["language"] = self.language
        self.apply_settings()
        self.retranslate()
        self.status_label.setText(self.tr("settings") + " — " + self.tr("ready"))

    def change_font_size(self, delta):
        self.values["font_size"] = max(7, min(36, int(self.values["font_size"]) + delta))
        self.editor.apply_settings()
        write_config(self.values)

    def update_title(self, *_):
        name = self.current_file.name if self.current_file else self.tr("untitled")
        dirty = " *" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{dirty} — {APP_NAME}")

    def update_cursor_status(self):
        cursor = self.editor.textCursor()
        self.cursor_label.setText(self.tr("line_col").format(line=cursor.blockNumber() + 1,
                                                              col=cursor.positionInBlock() + 1))

    def log(self, message):
        self.output_log.appendPlainText(message)

    def confirm_save_if_dirty(self):
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(self, APP_NAME, self.tr("unsaved"),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        if answer == QMessageBox.StandardButton.Save:
            return self.save_file()
        return answer == QMessageBox.StandardButton.Discard

    def new_file(self):
        if hasattr(self, "editor") and not self.confirm_save_if_dirty():
            return
        if hasattr(self, "_player_temp_files"):
            self.stop_player(cleanup=True)
        self.current_file = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self.update_title()
        self.status_label.setText(self.tr("new_file"))

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("open_mml"), str(self.project_root), self.tr("mml_files"))
        if path:
            self.load_file(Path(path))

    def load_file(self, path: Path):
        if not self.confirm_save_if_dirty():
            return
        try:
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                content = path.read_text(encoding="cp932")
        except OSError as exc:
            QMessageBox.critical(self, APP_NAME, str(exc))
            return
        self.stop_player(cleanup=True)
        self.current_file = path.resolve()
        self.project_root = self.current_file.parent
        self.editor.setPlainText(content)
        self.editor.document().setModified(False)
        self.set_explorer_path(self.project_root, add_history=True)
        self.update_title()
        self.status_label.setText(str(self.current_file))

    def open_explorer_item(self, index):
        path = Path(self.file_model.filePath(index))
        if path.is_dir():
            self.set_explorer_path(path, add_history=True)
        elif path.suffix.lower() in (".muc", ".mml"):
            self.load_file(path)
        else:
            try:
                if sys.platform == "win32":
                    os_startfile = getattr(__import__("os"), "startfile")
                    os_startfile(str(path))
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", str(path)])
            except Exception as exc:
                QMessageBox.warning(self, APP_NAME, str(exc))

    def save_file(self):
        if self.current_file is None:
            return self.save_file_as()
        try:
            self.current_file.write_text(self.editor.toPlainText(), encoding="utf-8", newline="\n")
            self.editor.document().setModified(False)
            self.update_title()
            self.status_label.setText(self.tr("saved") + str(self.current_file))
            return True
        except OSError as exc:
            QMessageBox.critical(self, APP_NAME, self.tr("save_failed") + str(exc))
            return False

    def save_file_as(self):
        start = str(self.current_file) if self.current_file else str(self.project_root / self.tr("untitled"))
        path, _ = QFileDialog.getSaveFileName(self, self.tr("save_mml"), start, self.tr("save_filter"))
        if not path:
            return False
        target = Path(path)
        if not target.suffix:
            target = target.with_suffix(".muc")
        self.current_file = target.resolve()
        self.project_root = self.current_file.parent
        self.set_explorer_path(self.project_root, add_history=True)
        return self.save_file()

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("open_folder"), str(self.project_root))
        if path:
            self.set_explorer_path(Path(path), add_history=True)

    def set_explorer_path(self, path, add_history=False):
        path = Path(path).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            QMessageBox.warning(self, APP_NAME, str(path))
            return False
        self.project_root = path
        self.values["explorer_path"] = str(path)
        self.file_model.setRootPath(str(path))
        self.explorer_table.setRootIndex(self.file_model.index(str(path)))
        self.path_edit.setText(str(path))
        if add_history:
            if self.history_index < 0 or self.history[self.history_index] != path:
                self.history = self.history[:self.history_index + 1]
                self.history.append(path)
                self.history_index = len(self.history) - 1
        self.back_button.setEnabled(self.history_index > 0)
        self.forward_button.setEnabled(self.history_index >= 0 and self.history_index < len(self.history) - 1)
        self.status_label.setText(str(path))
        return True

    def navigate_to_path(self):
        self.set_explorer_path(Path(self.path_edit.text()), add_history=True)

    def navigate_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.set_explorer_path(self.history[self.history_index])

    def navigate_forward(self):
        if self.history_index + 1 < len(self.history):
            self.history_index += 1
            self.set_explorer_path(self.history[self.history_index])

    def navigate_up(self):
        parent = self.project_root.parent
        if parent != self.project_root:
            self.set_explorer_path(parent, add_history=True)

    def refresh_explorer(self):
        path = self.project_root
        self.file_model.setRootPath("")
        self.file_model.setRootPath(str(path))
        self.explorer_table.setRootIndex(self.file_model.index(str(path)))

    def selected_paths(self):
        rows = self.explorer_table.selectionModel().selectedRows(0)
        return [Path(self.file_model.filePath(index)) for index in rows]

    def explorer_context_menu(self, pos):
        menu = QMenu(self)
        selected = self.selected_paths()
        new_folder = menu.addAction(self.tr("new_folder"))
        rename = menu.addAction(self.tr("rename"))
        delete = menu.addAction(self.tr("delete"))
        menu.addSeparator()
        copy = menu.addAction(self.tr("copy"))
        cut = menu.addAction(self.tr("cut"))
        paste = menu.addAction(self.tr("paste"))
        copy_path = menu.addAction(self.tr("copy_path"))
        rename.setEnabled(len(selected) == 1)
        delete.setEnabled(bool(selected))
        copy.setEnabled(bool(selected)); cut.setEnabled(bool(selected))
        paste.setEnabled(bool(self.clipboard_paths) or QApplication.clipboard().mimeData().hasUrls())
        copy_path.setEnabled(bool(selected))
        chosen = menu.exec(self.explorer_table.viewport().mapToGlobal(pos))
        if chosen == new_folder: self.explorer_new_folder()
        elif chosen == rename: self.explorer_rename()
        elif chosen == delete: self.explorer_delete()
        elif chosen == copy: self.explorer_copy(False)
        elif chosen == cut: self.explorer_copy(True)
        elif chosen == paste: self.explorer_paste()
        elif chosen == copy_path and selected: QApplication.clipboard().setText(str(selected[0]))

    def explorer_new_folder(self):
        name, ok = QInputDialog.getText(self, self.tr("new_folder"), self.tr("folder_name"))
        if ok and name.strip():
            target = self.project_root / name.strip()
            try:
                target.mkdir()
                self.refresh_explorer()
            except OSError as exc:
                QMessageBox.warning(self, APP_NAME, self.tr("file_operation_error") + str(exc))

    def explorer_rename(self):
        selected = self.selected_paths()
        if len(selected) != 1: return
        source = selected[0]
        name, ok = QInputDialog.getText(self, self.tr("rename"), self.tr("rename_prompt"), text=source.name)
        if not ok or not name.strip() or name.strip() == source.name: return
        target = source.with_name(name.strip())
        if target.exists():
            QMessageBox.warning(self, APP_NAME, self.tr("confirm_overwrite")); return
        try:
            source.rename(target); self.refresh_explorer()
        except OSError as exc:
            QMessageBox.warning(self, APP_NAME, self.tr("file_operation_error") + str(exc))

    def explorer_delete(self):
        paths = self.selected_paths()
        if not paths: return
        if QMessageBox.question(self, APP_NAME, self.tr("confirm_delete"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            for path in paths:
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
            self.refresh_explorer()
        except OSError as exc:
            QMessageBox.warning(self, APP_NAME, self.tr("file_operation_error") + str(exc))

    def explorer_copy(self, cut=False):
        paths = self.selected_paths()
        if not paths: return
        self.clipboard_paths = paths
        self.clipboard_cut = cut
        mime = QMimeData(); mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
        QApplication.clipboard().setMimeData(mime)

    def explorer_paste(self):
        mime = QApplication.clipboard().mimeData()
        paths = list(self.clipboard_paths)
        cut = self.clipboard_cut
        if not paths and mime.hasUrls():
            paths = [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]
            cut = False
        if paths:
            self.copy_paths_to(paths, self.project_root, move=cut)
            if cut:
                self.clipboard_paths = []; self.clipboard_cut = False

    def copy_paths_to(self, sources, destination, move=False):
        destination = Path(destination)
        for source in sources:
            try:
                if not source.exists(): continue
                target = destination / source.name
                if source.resolve() == target.resolve(): continue
                if target.exists():
                    answer = QMessageBox.question(self, APP_NAME, self.tr("confirm_overwrite") + "\n" + str(target), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if answer != QMessageBox.StandardButton.Yes: continue
                    if target.is_dir(): shutil.rmtree(target)
                    else: target.unlink()
                if move:
                    shutil.move(str(source), str(target))
                elif source.is_dir():
                    shutil.copytree(source, target)
                else:
                    shutil.copy2(source, target)
            except OSError as exc:
                QMessageBox.warning(self, APP_NAME, self.tr("file_operation_error") + str(exc))
        self.refresh_explorer()

    def open_find(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("find"))
        layout = QVBoxLayout(dialog)
        row = QHBoxLayout()
        row.addWidget(QLabel(self.tr("find_text")))
        field = QLineEdit(self.editor.textCursor().selectedText())
        row.addWidget(field, 1)
        layout.addLayout(row)
        buttons = QDialogButtonBox()
        next_button = buttons.addButton(self.tr("find_next"), QDialogButtonBox.ButtonRole.ActionRole)
        prev_button = buttons.addButton(self.tr("find_previous"), QDialogButtonBox.ButtonRole.ActionRole)
        close_button = buttons.addButton(self.tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        next_button.clicked.connect(lambda: self.find_text(False, field.text()))
        prev_button.clicked.connect(lambda: self.find_text(True, field.text()))
        close_button.clicked.connect(dialog.reject)
        layout.addWidget(buttons)
        field.returnPressed.connect(lambda: self.find_text(False, field.text()))
        field.textChanged.connect(self.editor.set_search_highlight)
        self.editor.set_search_highlight(field.text())
        dialog.finished.connect(lambda _result: self.editor.set_search_highlight(""))
        dialog.show()
        field.setFocus()
        self.find_dialog = dialog
        self.find_field = field

    def open_replace(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("replace"))
        layout = QVBoxLayout(dialog)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel(self.tr("find_text")))
        search_field = QLineEdit(self.editor.textCursor().selectedText())
        search_row.addWidget(search_field, 1)
        layout.addLayout(search_row)

        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel(self.tr("replace_text")))
        replace_field = QLineEdit()
        replace_row.addWidget(replace_field, 1)
        layout.addLayout(replace_row)

        buttons = QDialogButtonBox()
        next_button = buttons.addButton(self.tr("find_down"), QDialogButtonBox.ButtonRole.ActionRole)
        replace_all_button = buttons.addButton(self.tr("replace_all"), QDialogButtonBox.ButtonRole.ActionRole)
        close_button = buttons.addButton(self.tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        next_button.clicked.connect(
            lambda: self.replace_and_find_next(search_field.text(), replace_field.text())
        )
        replace_all_button.clicked.connect(lambda: self.replace_all(search_field.text(), replace_field.text()))
        close_button.clicked.connect(dialog.reject)
        layout.addWidget(buttons)
        search_field.returnPressed.connect(
            lambda: self.replace_and_find_next(search_field.text(), replace_field.text())
        )
        # Keep exactly one current replacement target selected/highlighted.
        # Updating the search term immediately selects the first matching occurrence;
        # F3 then replaces that occurrence and advances to the next one.
        search_field.textChanged.connect(self._update_replace_target)
        self._update_replace_target(search_field.text())
        dialog.finished.connect(lambda _result: self.editor.set_search_highlight(""))

        self.find_dialog = dialog
        self.find_field = search_field
        self.replace_dialog = dialog
        self.replace_search_field = search_field
        self.replace_field = replace_field
        dialog.show()
        search_field.setFocus()
        search_field.selectAll()

    def _update_replace_target(self, search_term):
        """Select and highlight only the next occurrence to be replaced."""
        self.editor.set_search_highlight(search_term)
        if not search_term:
            return
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        found = self.editor.find(search_term, QTextDocument.FindFlag(0))
        if not found:
            self.editor.set_search_highlight(search_term)
            self.status_label.setText(self.tr("not_found") + search_term)

    def _handle_f3(self):
        """F3 searches normally, but in the Replace dialog it replaces and advances."""
        if getattr(self, "replace_dialog", None) is not None and self.replace_dialog.isVisible():
            self.replace_and_find_next(
                self.replace_search_field.text(), self.replace_field.text()
            )
        else:
            self.find_text(False)

    def replace_and_find_next(self, search_term, replacement):
        """Replace one occurrence, then select the next occurrence of the search term."""
        if not search_term:
            self.status_label.setText(self.tr("not_found"))
            return

        editor = self.editor
        cursor = editor.textCursor()
        replaced = False

        # If the current selection is the requested term, replace that selection.
        if cursor.hasSelection() and cursor.selectedText() == search_term:
            cursor.insertText(replacement)
            editor.setTextCursor(cursor)
            replaced = True
        else:
            # Otherwise, locate the next occurrence first and replace it.
            found = editor.find(search_term, QTextDocument.FindFlag(0))
            if not found:
                cursor = editor.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                editor.setTextCursor(cursor)
                found = editor.find(search_term, QTextDocument.FindFlag(0))
            if not found:
                self.status_label.setText(self.tr("not_found") + search_term)
                return
            cursor = editor.textCursor()
            cursor.insertText(replacement)
            editor.setTextCursor(cursor)
            replaced = True

        if replaced:
            # Search from the position immediately after the inserted replacement.
            found_next = editor.find(search_term, QTextDocument.FindFlag(0))
            if not found_next:
                cursor = editor.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                editor.setTextCursor(cursor)
                found_next = editor.find(search_term, QTextDocument.FindFlag(0))
            editor.setFocus()
            self.editor.set_search_highlight(search_term)
            self.status_label.setText(self.tr("replace_count").format(count=1))

    def find_text(self, backwards=False, term=None):
        if term is None:
            term = self.find_field.text() if hasattr(self, "find_field") else ""
        if not term:
            self.open_find()
            return
        flags = QTextDocument.FindFlag.FindBackward if backwards else QTextDocument.FindFlag(0)
        found = self.editor.find(term, flags)
        if not found:
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End if backwards else cursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(term, flags)
        self.editor.set_search_highlight(term)
        if not found:
            self.status_label.setText(self.tr("not_found") + term)

    def replace_all(self, search_term, replacement):
        if not search_term:
            self.status_label.setText(self.tr("not_found"))
            return

        # Collect matches from the original document first, then replace backwards.
        # This preserves the editor's undo history and avoids re-matching inserted text.
        document = self.editor.document()
        search_cursor = QTextCursor(document)
        matches = []
        while True:
            match = document.find(search_term, search_cursor, QTextDocument.FindFlag(0))
            if match.isNull():
                break
            matches.append((match.selectionStart(), match.selectionEnd()))
            search_cursor.setPosition(match.selectionEnd())

        if not matches:
            self.status_label.setText(self.tr("not_found") + search_term)
            return

        edit_cursor = QTextCursor(document)
        edit_cursor.beginEditBlock()
        try:
            # Replace from the end so earlier recorded positions remain valid.
            for start, end in reversed(matches):
                edit_cursor.setPosition(start)
                edit_cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                edit_cursor.insertText(replacement)
        finally:
            edit_cursor.endEditBlock()

        # Move the editor cursor to the first replaced location and make the change visible.
        first_start = matches[0][0]
        edit_cursor.setPosition(first_start)
        self.editor.setTextCursor(edit_cursor)
        self.editor.set_search_highlight(search_term)
        self.editor.setFocus()
        self.status_label.setText(self.tr("replace_count").format(count=len(matches)))

    def save_and_compile(self):
        if self.save_file():
            self.compile_file(skip_save=True)








    def compile_file(self, skip_save=False):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.log(self.tr("compile_running"))
            return
        if (not skip_save and not self.save_file()) or self.current_file is None:
            return
        compiler = Path(self.values["compiler_path"]).expanduser()
        candidates = [self.current_file.parent / "mucomvgm.exe", BASE_DIR / "mucomvgm.exe"]
        if not compiler.is_file():
            compiler = next((p for p in candidates if p.is_file()), compiler)
        if not compiler.is_file():
            QMessageBox.warning(self, APP_NAME, self.tr("compiler_missing"))
            return
        self.log("\n" + "=" * 60)
        self.log(self.tr("compile_start") + f'"{compiler}" "{self.current_file.name}"')
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(self.current_file.parent))
        self.process.setProgram(str(compiler.resolve()))
        self.process.setArguments([self.current_file.name])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_process_output)
        self.process.finished.connect(self.compile_finished)
        self.process.errorOccurred.connect(lambda _error: self.log(self.tr("compile_error") + self.process.errorString()))
        self.process.start()
        self.status_label.setText(self.tr("compile_running"))

    def read_process_output(self):
        if self.process:
            output = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace").rstrip()
            if output:
                self.log(output)

    def compile_finished(self, exit_code, exit_status):
        self.read_process_output()
        if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            output = self.current_file.with_suffix(".vgm") if self.current_file else None
            if output and output.exists():
                self.log(self.tr("compile_success") + str(output))
            else:
                self.log(self.tr("no_output") + (str(output) if output else "*.vgm"))
        else:
            self.log(self.tr("compile_failed") + str(exit_code) + ")")
        self.status_label.setText(self.tr("ready"))
        self.process.deleteLater()
        self.process = None

    def closeEvent(self, event):
        if not self.confirm_save_if_dirty():
            event.ignore()
            return
        self.values["explorer_path"] = str(self.project_root)
        self.values["window_geometry"] = bytes(self.saveGeometry()).hex()
        self.values["window_state"] = bytes(self.saveState()).hex()
        self.values["explorer_width"] = self.explorer_dock.width()
        self.values["output_height"] = self.output_dock.height()
        self.values["explorer_sort_column"] = self.explorer_table.horizontalHeader().sortIndicatorSection()
        self.values["explorer_sort_order"] = (
            "descending" if self.explorer_table.horizontalHeader().sortIndicatorOrder() == Qt.SortOrder.DescendingOrder
            else "ascending"
        )
        self.values["explorer_column_widths"] = [
            self.explorer_table.columnWidth(i) for i in range(self.explorer_table.model().columnCount())
        ]
        try:
            saved_to = write_config(self.values)
            self.log(f"Settings saved: {saved_to}")
        except OSError as exc:
            QMessageBox.warning(self, APP_NAME, f"設定を保存できませんでした: {exc}")
            event.ignore()
            return
        self.stop_player(cleanup=True)
        event.accept()

