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

from .config import COLOR_KEYS, TEXT, THEMES

class SettingsDialog(QDialog):
    def __init__(self, values, language, parent=None, on_apply=None):
        super().__init__(parent)
        self.on_apply = on_apply
        self.values = json.loads(json.dumps(values))
        self.language = language
        self.labels = TEXT.get(language, TEXT["Japanese"])
        self.setWindowTitle(self.labels["settings"])
        self.resize(620, 650)
        root = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Japanese", "English"])
        self.language_combo.setCurrentText(self.values["language"])
        form.addRow(self.labels["language"], self.language_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark", "Custom"])
        self.theme_combo.setCurrentText(self.values["theme"])
        self.theme_combo.currentTextChanged.connect(self.theme_changed)
        form.addRow(self.labels["theme"], self.theme_combo)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(7, 36)
        self.font_spin.setSuffix(" pt")
        self.font_spin.setValue(int(self.values["font_size"]))
        form.addRow(self.labels["font_size"], self.font_spin)

        compiler_row = QWidget()
        compiler_layout = QHBoxLayout(compiler_row)
        compiler_layout.setContentsMargins(0, 0, 0, 0)
        self.compiler_edit = QLineEdit(self.values["compiler_path"])
        browse = QPushButton(self.labels["browse"])
        browse.clicked.connect(self.browse_compiler)
        compiler_layout.addWidget(self.compiler_edit, 1)
        compiler_layout.addWidget(browse)
        form.addRow(self.labels["compiler_path"], compiler_row)

        self.line_numbers_check = QCheckBox(self.labels["show_line_numbers"])
        self.line_numbers_check.setChecked(self.values["show_line_numbers"])
        form.addRow("", self.line_numbers_check)
        self.ruler_check = QCheckBox(self.labels["show_ruler"])
        self.ruler_check.setChecked(self.values["show_ruler"])
        form.addRow("", self.ruler_check)
        self.underline_check = QCheckBox(self.labels["current_line_underline"])
        self.underline_check.setChecked(self.values["show_current_line_underline"])
        form.addRow("", self.underline_check)

        self.color_buttons = {}
        colors_group = QGroupBox(self.labels["colors"])
        colors_form = QFormLayout(colors_group)
        color_names = {
            "editor_background": "color_editor_background", "editor_foreground": "color_editor_foreground",
            "line_number_background": "color_line_number_background", "line_number_foreground": "color_line_number_foreground",
            "current_line_underline": "color_current_line_underline", "ruler_background": "color_ruler_background",
            "ruler_foreground": "color_ruler_foreground", "comment": "color_comment", "directive": "color_directive",
            "parameter": "color_parameter", "macro": "color_macro", "number": "color_number",
            "search_match": "color_search_match",
        }
        for key in COLOR_KEYS:
            button = QPushButton(self.values["colors"][key])
            button.setStyleSheet(f"background-color: {self.values['colors'][key]};")
            button.clicked.connect(lambda checked=False, k=key: self.choose_color(k))
            self.color_buttons[key] = button
            colors_form.addRow(self.labels[color_names[key]], button)
        form.addRow(colors_group)
        scroll.setWidget(content)
        root.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel |
                                   QDialogButtonBox.StandardButton.Apply)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.labels["ok"])
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.labels["cancel"])
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText(self.labels["apply"])
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_values)
        root.addWidget(buttons)

    def theme_changed(self, theme):
        if theme in ("Light", "Dark"):
            self.values["colors"].update(THEMES[theme])
            for key, button in self.color_buttons.items():
                button.setText(self.values["colors"][key])
                button.setStyleSheet(f"background-color: {self.values['colors'][key]};")

    def choose_color(self, key):
        color = QColorDialog.getColor(QColor(self.values["colors"][key]), self)
        if color.isValid():
            self.values["colors"][key] = color.name()
            self.theme_combo.setCurrentText("Custom")
            button = self.color_buttons[key]
            button.setText(color.name())
            button.setStyleSheet(f"background-color: {color.name()};")

    def browse_compiler(self):
        path, _ = QFileDialog.getOpenFileName(self, self.labels["select_compiler"], self.compiler_edit.text(),
                                              self.labels["exe_filter"])
        if path:
            self.compiler_edit.setText(path)

    def collect_values(self):
        self.values["language"] = self.language_combo.currentText()
        self.values["theme"] = self.theme_combo.currentText()
        self.values["font_size"] = self.font_spin.value()
        self.values["compiler_path"] = self.compiler_edit.text().strip()
        self.values["show_line_numbers"] = self.line_numbers_check.isChecked()
        self.values["show_ruler"] = self.ruler_check.isChecked()
        self.values["show_current_line_underline"] = self.underline_check.isChecked()
        return self.values

    def apply_values(self):
        self.collect_values()
        if self.on_apply:
            self.on_apply(self.values)

