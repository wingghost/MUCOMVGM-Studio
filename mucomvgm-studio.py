from __future__ import annotations

import configparser
import json
import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRect, QSize, QProcess
from PySide6.QtGui import (
    QAction, QColor, QFont, QPainter, QTextCharFormat, QSyntaxHighlighter,
    QTextFormat, QKeySequence, QShortcut, QTextDocument, QTextCursor, QPainterPath,
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QDockWidget,
    QFileDialog, QFileSystemModel, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSpinBox, QStatusBar, QToolBar, QTreeView, QVBoxLayout, QWidget,
    QTabWidget, QColorDialog, QCheckBox, QGroupBox, QScrollArea, QTextEdit,
)

APP_NAME = "MUCOMVGM Studio"
APP_ORG = "WINGGHOST"
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "mucomvgm-studio.ini"
LOCALES_DIR = BASE_DIR / "locales"

DEFAULTS = {
    "language": "Japanese",
    "compiler_path": str(BASE_DIR / "mucomvgm.exe"),
    "theme": "Dark",
    "font_size": "12",
    "show_line_numbers": "true",
    "show_ruler": "true",
    "show_current_line_underline": "true",
    "colors": {
        "editor_background": "#1E1E1E",
        "editor_foreground": "#D4D4D4",
        "line_number_background": "#252526",
        "line_number_foreground": "#858585",
        "current_line_underline": "#569CD6",
        "ruler_background": "#252526",
        "ruler_foreground": "#858585",
        "comment": "#6A9955",
        "directive": "#C586C0",
        "parameter": "#DCDCAA",
        "macro": "#D7BA7D",
        "number": "#B5CEA8",
    },
}
THEMES = {
    "Dark": {
        "editor_background": "#1E1E1E", "editor_foreground": "#D4D4D4",
        "line_number_background": "#252526", "line_number_foreground": "#858585",
        "current_line_underline": "#569CD6", "ruler_background": "#252526",
        "ruler_foreground": "#858585", "comment": "#6A9955",
        "directive": "#C586C0", "parameter": "#DCDCAA", "macro": "#D7BA7D",
        "number": "#B5CEA8",
    },
    "Light": {
        "editor_background": "#FFFFFF", "editor_foreground": "#202020",
        "line_number_background": "#F0F0F0", "line_number_foreground": "#777777",
        "current_line_underline": "#007ACC", "ruler_background": "#F0F0F0",
        "ruler_foreground": "#777777", "comment": "#008000",
        "directive": "#AF00DB", "parameter": "#795E26", "macro": "#A31515",
        "number": "#098658",
    },
    "System": {},
}

TEXT = {
    "Japanese": {
        "file": "ファイル", "edit": "編集", "view": "表示", "tools": "ツール", "help": "ヘルプ",
        "settings": "設定", "new": "新規作成", "open": "開く…", "save": "保存",
        "save_as": "名前を付けて保存…", "compile": "コンパイル", "open_folder": "フォルダーを開く…",
        "exit": "終了", "explorer": "エクスプローラー", "output": "出力", "ready": "準備完了",
        "open_mml": "MMLファイルを開く", "mml_files": "MMLファイル (*.muc *.mml);;すべてのファイル (*)",
        "save_mml": "MMLファイルを保存", "save_filter": "MMLファイル (*.muc);;すべてのファイル (*)",
        "untitled": "無題.muc", "unsaved": "未保存の変更があります。保存しますか？",
        "compiler_missing": "mucomvgm.exe が見つかりません。「設定」から指定してください。",
        "select_compiler": "mucomvgm.exe を選択", "exe_filter": "実行ファイル (*.exe);;すべてのファイル (*)",
        "compile_start": "コンパイル開始: ", "compile_success": "コンパイル成功: ",
        "compile_failed": "コンパイル失敗 (終了コード: ", "compile_running": "コンパイル中…",
        "saved": "保存しました: ", "save_failed": "保存できませんでした: ",
        "compile_error": "コンパイルを開始できませんでした: ", "no_output": "想定されたVGMファイルが見つかりません: ",
        "line_col": "行 {line}, 列 {col}", "new_file": "新規MML", "about": "MUCOMVGM Studio (MVS) 試作版",
        "about_title": "このアプリについて", "language": "言語", "theme": "テーマ",
        "font_size": "エディター文字サイズ", "compiler_path": "mucomvgm.exe のパス",
        "browse": "参照…", "show_line_numbers": "行番号を表示", "show_ruler": "列ルーラーを表示",
        "current_line_underline": "カーソル行に下線を表示", "appearance": "表示", "colors": "配色のカスタマイズ",
        "color_editor_background": "エディター背景", "color_editor_foreground": "エディター文字",
        "color_line_number_background": "行番号背景", "color_line_number_foreground": "行番号文字",
        "color_current_line_underline": "カーソル行の下線", "color_ruler_background": "ルーラー背景",
        "color_ruler_foreground": "ルーラー文字", "color_comment": "コメント", "color_directive": "ディレクティブ",
        "color_parameter": "コマンド／パラメーター", "color_macro": "マクロ／@コマンド", "color_number": "数値",
        "apply": "適用", "ok": "OK", "cancel": "キャンセル", "find": "検索", "find_next": "次を検索",
        "find_previous": "前を検索", "find_text": "検索文字列", "not_found": "見つかりません: ",
        "clear_output": "ログをクリア", "undo": "元に戻す", "redo": "やり直し",
        "cut": "切り取り", "copy": "コピー", "paste": "貼り付け",
    },
    "English": {
        "file": "File", "edit": "Edit", "view": "View", "tools": "Tools", "help": "Help",
        "settings": "Settings", "new": "New", "open": "Open…", "save": "Save",
        "save_as": "Save As…", "compile": "Compile", "open_folder": "Open Folder…",
        "exit": "Exit", "explorer": "Explorer", "output": "Output", "ready": "Ready",
        "open_mml": "Open MML File", "mml_files": "MML files (*.muc *.mml);;All files (*)",
        "save_mml": "Save MML File", "save_filter": "MML files (*.muc);;All files (*)",
        "untitled": "Untitled.muc", "unsaved": "There are unsaved changes. Save them?",
        "compiler_missing": "mucomvgm.exe was not found. Set its path in Settings.",
        "select_compiler": "Select mucomvgm.exe", "exe_filter": "Executable (*.exe);;All files (*)",
        "compile_start": "Compiling: ", "compile_success": "Compile succeeded: ",
        "compile_failed": "Compile failed (exit code: ", "compile_running": "Compiling…",
        "saved": "Saved: ", "save_failed": "Could not save file: ",
        "compile_error": "Could not start compiler: ", "no_output": "Expected VGM output was not found: ",
        "line_col": "Line {line}, Col {col}", "new_file": "New MML", "about": "MUCOMVGM Studio (MVS) prototype",
        "about_title": "About", "language": "Language", "theme": "Theme",
        "font_size": "Editor font size", "compiler_path": "mucomvgm.exe path",
        "browse": "Browse…", "show_line_numbers": "Show line numbers", "show_ruler": "Show column ruler",
        "current_line_underline": "Underline current line", "appearance": "Appearance", "colors": "Customize colors",
        "color_editor_background": "Editor background", "color_editor_foreground": "Editor text",
        "color_line_number_background": "Line number background", "color_line_number_foreground": "Line number text",
        "color_current_line_underline": "Current-line underline", "color_ruler_background": "Ruler background",
        "color_ruler_foreground": "Ruler text", "color_comment": "Comments", "color_directive": "Directives",
        "color_parameter": "Commands / parameters", "color_macro": "Macros / @ commands", "color_number": "Numbers",
        "apply": "Apply", "ok": "OK", "cancel": "Cancel", "find": "Find", "find_next": "Find Next",
        "find_previous": "Find Previous", "find_text": "Search text", "not_found": "Not found: ",
        "clear_output": "Clear Log", "undo": "Undo", "redo": "Redo", "cut": "Cut", "copy": "Copy", "paste": "Paste",
    },
}
COLOR_KEYS = [
    "editor_background", "editor_foreground", "line_number_background", "line_number_foreground",
    "current_line_underline", "ruler_background", "ruler_foreground", "comment", "directive",
    "parameter", "macro", "number",
]

def read_config():
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        try:
            config.read(CONFIG_PATH, encoding="utf-8")
        except (OSError, configparser.Error):
            pass
    values = {
        "language": config.get("General", "language", fallback=DEFAULTS["language"]),
        "compiler_path": config.get("General", "compiler_path", fallback=DEFAULTS["compiler_path"]),
        "theme": config.get("Appearance", "theme", fallback=DEFAULTS["theme"]),
        "font_size": config.getint("Appearance", "font_size", fallback=int(DEFAULTS["font_size"])),
        "show_line_numbers": config.getboolean("Appearance", "show_line_numbers", fallback=True),
        "show_ruler": config.getboolean("Appearance", "show_ruler", fallback=True),
        "show_current_line_underline": config.getboolean("Appearance", "show_current_line_underline", fallback=True),
        "colors": dict(DEFAULTS["colors"]),
    }
    for key in COLOR_KEYS:
        values["colors"][key] = config.get("Colors", key, fallback=values["colors"][key])
    return values

def write_config(values):
    config = configparser.ConfigParser()
    config["General"] = {
        "language": str(values["language"]),
        "compiler_path": str(values["compiler_path"]),
    }
    config["Appearance"] = {
        "theme": str(values["theme"]),
        "font_size": str(values["font_size"]),
        "show_line_numbers": str(values["show_line_numbers"]).lower(),
        "show_ruler": str(values["show_ruler"]).lower(),
        "show_current_line_underline": str(values["show_current_line_underline"]).lower(),
    }
    config["Colors"] = {key: str(values["colors"].get(key, DEFAULTS["colors"][key])) for key in COLOR_KEYS}
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as stream:
            config.write(stream)
    except OSError:
        # The UI remains usable if the directory is read-only; caller can report if needed.
        pass

class MmlHighlighter(QSyntaxHighlighter):
    """Lightweight highlighter: deliberately leaves note letters uncolored."""
    def __init__(self, document, get_colors):
        super().__init__(document)
        self.get_colors = get_colors
        self.rules = [
            (re.compile(r";.*$"), "comment"),
            (re.compile(r"//.*$"), "comment"),
            (re.compile(r"#(?:[A-Za-z_][A-Za-z0-9_]*|[0-9]+)"), "directive"),
            (re.compile(r"@[A-Za-z0-9_%]+"), "macro"),
            (re.compile(r"\b(?:EX|EX2|YM|OP|FB|ALG|AMS|FMS|LFO|PAN|P|Q|T|V|O|L|K|S|W|Y|Z)[+-]?\d*\b", re.IGNORECASE), "parameter"),
            (re.compile(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?"), "number"),
        ]

    def highlightBlock(self, text):
        colors = self.get_colors()
        for pattern, key in self.rules:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(colors.get(key, DEFAULTS["colors"].get(key, "#D4D4D4"))))
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)

class ColumnRuler(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedHeight(24)

    def paintEvent(self, event):
        self.editor.paint_ruler(event)

class CurrentLineOverlay(QWidget):
    """Transparent overlay that paints the current-line underline across the viewport."""
    def __init__(self, editor):
        super().__init__(editor.viewport())
        self.editor = editor
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    def paintEvent(self, event):
        settings = self.editor.settings_getter()
        if not settings["show_current_line_underline"]:
            return
        block = self.editor.textCursor().block()
        if not block.isValid() or not block.isVisible():
            return
        rect = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).toRect()
        y = rect.bottom()
        if 0 <= y < self.height():
            painter = QPainter(self)
            painter.setPen(QColor(settings["colors"]["current_line_underline"]))
            painter.drawLine(0, y, self.width() - 1, y)

class MmlEditor(QPlainTextEdit):
    def __init__(self, settings_getter, parent=None):
        super().__init__(parent)
        self.settings_getter = settings_getter
        self.line_number_area = LineNumberArea(self)
        self.ruler = ColumnRuler(self)
        self.highlighter = MmlHighlighter(self.document(), self.syntax_colors)
        self.current_line_overlay = CurrentLineOverlay(self)
        self.setFont(self.make_font())
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.update_extra_selections)
        self.cursorPositionChanged.connect(self.update_ruler_marker)
        self.horizontalScrollBar().valueChanged.connect(self.ruler.update)
        self.horizontalScrollBar().valueChanged.connect(self.update_current_line_overlay)
        self.verticalScrollBar().valueChanged.connect(self.update_current_line_overlay)
        self.update_line_number_width()
        self.update_extra_selections()
        self.update_current_line_overlay()

    def update_current_line_overlay(self, *_):
        if not hasattr(self, "current_line_overlay"):
            return
        self.current_line_overlay.setGeometry(self.viewport().rect())
        self.current_line_overlay.setVisible(self.settings_getter()["show_current_line_underline"])
        self.current_line_overlay.update()

    def update_ruler_marker(self, *_):
        if hasattr(self, "ruler"):
            self.ruler.update()

    def make_font(self):
        font = QFont("Consolas", int(self.settings_getter()["font_size"]))
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font

    def syntax_colors(self):
        colors = self.settings_getter()["colors"]
        return {
            "comment": colors["comment"], "directive": colors["directive"],
            "parameter": colors["parameter"], "macro": colors["macro"], "number": colors["number"],
        }

    def apply_settings(self):
        settings = self.settings_getter()
        font = self.make_font()
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        colors = settings["colors"]
        palette = self.palette()
        palette.setColor(palette.ColorRole.Base, QColor(colors["editor_background"]))
        palette.setColor(palette.ColorRole.Text, QColor(colors["editor_foreground"]))
        self.setPalette(palette)
        self.line_number_area.setVisible(settings["show_line_numbers"])
        self.ruler.setVisible(settings["show_ruler"])
        self.highlighter.rehighlight()
        self.update_line_number_width()
        self.update_extra_selections()
        self.line_number_area.update()
        self.ruler.update()
        self.update_current_line_overlay()
        self.viewport().update()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            settings = self.settings_getter()
            delta = event.angleDelta().y()
            if delta:
                settings["font_size"] = max(7, min(36, int(settings["font_size"]) + (1 if delta > 0 else -1)))
                self.apply_settings()
                event.accept()
                return
        super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        ruler_height = 24 if self.settings_getter()["show_ruler"] else 0
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top() + ruler_height,
                                                self.line_number_area_width(), max(0, cr.height() - ruler_height)))
        self.ruler.setGeometry(QRect(cr.left() + self.line_number_area_width(), cr.top(),
                                     max(0, cr.width() - self.line_number_area_width()), 24))
        self.update_current_line_overlay()

    def line_number_area_width(self):
        if not self.settings_getter()["show_line_numbers"]:
            return 0
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_width(self, *_):
        top_margin = 24 if self.settings_getter()["show_ruler"] else 0
        self.setViewportMargins(self.line_number_area_width(), top_margin, 0, 0)
        self.line_number_area.update()
        self.ruler.setVisible(self.settings_getter()["show_ruler"])

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_width()
        self.ruler.update()
        self.update_current_line_overlay()

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        colors = self.settings_getter()["colors"]
        painter.fillRect(event.rect(), QColor(colors["line_number_background"]))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        painter.setPen(QColor(colors["line_number_foreground"]))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, top, self.line_number_area.width() - 5,
                                 self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight,
                                 str(number + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            number += 1

    def paint_ruler(self, event):
        painter = QPainter(self.ruler)
        colors = self.settings_getter()["colors"]
        painter.fillRect(event.rect(), QColor(colors["ruler_background"]))
        painter.setPen(QColor(colors["ruler_foreground"]))
        char_width = max(1, self.fontMetrics().horizontalAdvance("9"))
        scroll_px = self.horizontalScrollBar().value()
        # Column 1 begins at the editor text origin; ticks use the same monospace cell width.
        x_origin = 4 - (scroll_px % char_width)
        visible_first = max(1, int(scroll_px / char_width) + 1)
        visible_last = visible_first + int(self.ruler.width() / char_width) + 2
        baseline = self.ruler.height() - 2
        for col in range(visible_first, visible_last + 1):
            x = x_origin + (col - 1) * char_width
            if x < 0 or x > self.ruler.width():
                continue
            if col % 10 == 0:
                painter.drawLine(x, 14, x, baseline)
                painter.drawText(x + 2, 12, str(col))
            elif col % 5 == 0:
                painter.drawLine(x, 17, x, baseline)
            else:
                painter.drawLine(x, 20, x, baseline)

        # A small down-pointing triangle tracks the current insertion column.
        cursor = self.textCursor()
        col = cursor.positionInBlock() + 1
        marker_x = x_origin + (col - 1) * char_width
        if -5 <= marker_x <= self.ruler.width() + 5:
            marker = QPainterPath()
            marker.moveTo(marker_x - 4, 1)
            marker.lineTo(marker_x + 4, 1)
            marker.lineTo(marker_x, 7)
            marker.closeSubpath()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(colors["current_line_underline"]))
            painter.drawPath(marker)

    def update_extra_selections(self):
        settings = self.settings_getter()
        selections = []
        # The full-width underline is painted by CurrentLineOverlay, including on blank lines.
        self.setExtraSelections(selections)

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.values = read_config()
        self.language = self.values["language"] if self.values["language"] in TEXT else "Japanese"
        self.values["language"] = self.language
        self.current_file: Path | None = None
        self.project_root = Path.cwd()
        self.process: QProcess | None = None
        self._build_ui()
        self.retranslate()
        self.apply_settings()
        self.new_file()
        self.resize(1200, 780)

    def tr(self, key):
        return TEXT.get(self.language, TEXT["Japanese"]).get(key, TEXT["Japanese"].get(key, key))

    def _build_ui(self):
        self.editor = MmlEditor(lambda: self.values)
        self.editor.document().modificationChanged.connect(self.update_title)
        self.editor.cursorPositionChanged.connect(self.update_cursor_status)
        self.setCentralWidget(self.editor)

        self.file_model = QFileSystemModel(self)
        self.file_model.setNameFilters(["*.muc", "*.mml", "*.vgm", "*.dat", "*.bin", "*.txt"])
        self.file_model.setNameFilterDisables(False)
        self.tree = QTreeView()
        self.tree.setModel(self.file_model)
        self.tree.doubleClicked.connect(self.open_tree_item)
        self.tree.setHeaderHidden(True)
        for col in range(1, 4):
            self.tree.hideColumn(col)
        self.explorer_dock = QDockWidget(self)
        self.explorer_dock.setWidget(self.tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_dock)

        self.output_log = QPlainTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setFont(QFont("Consolas", 9))
        self.output_dock = QDockWidget(self)
        self.output_dock.setWidget(self.output_log)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.actions = {}
        for key, callback in (("new", self.new_file), ("open", self.open_file),
                              ("save", self.save_file), ("compile", self.compile_file)):
            action = QAction(self)
            action.triggered.connect(callback)
            toolbar.addAction(action)
            self.actions[key] = action
        self.action_settings = QAction(self)
        self.action_settings.triggered.connect(self.open_settings)
        toolbar.addAction(self.action_settings)

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
        for key in ("new", "open", "save", "compile"):
            self.menu_file.addAction(self.actions[key])
        self.action_save_as = QAction(self)
        self.action_save_as.triggered.connect(self.save_file_as)
        self.menu_file.addAction(self.action_save_as)
        self.action_open_folder = QAction(self)
        self.action_open_folder.triggered.connect(self.open_folder)
        self.menu_file.addAction(self.action_open_folder)
        self.action_exit = QAction(self)
        self.action_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.action_exit)
        for key, callback in (("undo", self.editor.undo), ("redo", self.editor.redo),
                              ("cut", self.editor.cut), ("copy", self.editor.copy), ("paste", self.editor.paste)):
            action = QAction(self)
            action.triggered.connect(callback)
            self.menu_edit.addAction(action)
            self.actions[key] = action
        self.menu_view.addAction(self.explorer_dock.toggleViewAction())
        self.menu_view.addAction(self.output_dock.toggleViewAction())
        self.menu_tools.addAction(self.action_settings)
        self.action_clear_output = QAction(self)
        self.action_clear_output.triggered.connect(self.output_log.clear)
        self.menu_tools.addAction(self.action_clear_output)
        self.action_about = QAction(self)
        self.action_about.triggered.connect(lambda: QMessageBox.about(self, self.tr("about_title"), self.tr("about")))
        self.menu_help.addAction(self.action_about)

        self.find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        self.find_shortcut.activated.connect(self.open_find)
        self.find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        self.find_next_shortcut.activated.connect(lambda: self.find_text(False))
        self.find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
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
        self.explorer_dock.setWindowTitle(self.tr("explorer"))
        self.output_dock.setWindowTitle(self.tr("output"))
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
        self.current_file = path.resolve()
        self.project_root = self.current_file.parent
        self.editor.setPlainText(content)
        self.editor.document().setModified(False)
        self.file_model.setRootPath(str(self.project_root))
        self.tree.setRootIndex(self.file_model.index(str(self.project_root)))
        self.update_title()
        self.status_label.setText(str(self.current_file))

    def open_tree_item(self, index):
        path = Path(self.file_model.filePath(index))
        if path.is_file() and path.suffix.lower() in (".muc", ".mml"):
            self.load_file(path)

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
        self.file_model.setRootPath(str(self.project_root))
        self.tree.setRootIndex(self.file_model.index(str(self.project_root)))
        return self.save_file()

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("open_folder"), str(self.project_root))
        if path:
            self.project_root = Path(path)
            self.file_model.setRootPath(path)
            self.tree.setRootIndex(self.file_model.index(path))
            self.status_label.setText(path)

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
        dialog.show()
        field.setFocus()
        self.find_dialog = dialog
        self.find_field = field

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
        if not found:
            self.status_label.setText(self.tr("not_found") + term)

    def compile_file(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.log(self.tr("compile_running"))
            return
        if not self.save_file() or self.current_file is None:
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
        write_config(self.values)
        event.accept() if self.confirm_save_if_dirty() else event.ignore()

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
