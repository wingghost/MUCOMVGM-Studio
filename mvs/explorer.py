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


class ExplorerFileSystemModel(QFileSystemModel):
    """Filesystem model with human-readable sizes and a dash for directories."""
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            owner = self.parent()
            labels = ["name", "size", "type", "modified"]
            if 0 <= section < len(labels) and hasattr(owner, "tr"):
                return owner.tr(labels[section])
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and index.isValid() and index.column() == 1:
            info = self.fileInfo(index)
            if info.isDir():
                return "—"
            size = info.size()
            if size < 1024:
                return f"{size} B"
            if size < 1024 ** 2:
                return f"{size / 1024:.1f} KB"
            if size < 1024 ** 3:
                return f"{size / (1024 ** 2):.1f} MB"
            return f"{size / (1024 ** 3):.2f} GB"
        return super().data(index, role)


class ExplorerTable(QTableView):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.owner.explorer_context_menu)
        self.doubleClicked.connect(self.owner.open_explorer_item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            dest = self.owner.project_root
            paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
            mods = event.keyboardModifiers()
            if mods & Qt.KeyboardModifier.ShiftModifier:
                move = True
            elif mods & Qt.KeyboardModifier.ControlModifier:
                move = False
            else:
                try:
                    dest_drive = Path(dest).drive.casefold()
                    source_drives = {p.drive.casefold() for p in paths}
                    move = bool(dest_drive and source_drives == {dest_drive})
                except Exception:
                    move = False
            self.owner.copy_paths_to(paths, dest, move=move)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
            self.owner.explorer_copy(cut=False); return
        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_X:
            self.owner.explorer_copy(cut=True); return
        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
            self.owner.explorer_paste(); return
        if key == Qt.Key.Key_Delete:
            self.owner.explorer_delete(); return
        if key == Qt.Key.Key_F2:
            self.owner.explorer_rename(); return
        if key == Qt.Key.Key_Backspace:
            self.owner.navigate_up(); return
        super().keyPressEvent(event)

