from __future__ import annotations

import configparser
import json
import re
import sys
import os
import shutil
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

APP_NAME = "MUCOMVGM Studio"
APP_ORG = "WINGGHOST"
# In a PyInstaller one-file build, __file__ points into the temporary extraction
# directory. Use the executable directory for user-visible files instead.
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "mucomvgm-studio.ini"
APPDATA_CONFIG_PATH = Path(os.environ.get("APPDATA", str(Path.home() / ".config"))) / APP_ORG / APP_NAME / "mucomvgm-studio.ini"
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
        "settings": "設定", "new": "新規作成", "open": "開く…", "save": "上書き保存", "save_compile": "保存＆コンパイル",
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
        "cut": "切り取り", "copy": "コピー", "paste": "貼り付け", "select_all": "すべて選択",
        "back": "戻る", "forward": "進む", "up": "上へ", "refresh": "更新", "new_folder": "新しいフォルダー",
        "delete": "削除", "rename": "名前の変更", "copy_path": "パスをコピー", "size": "サイズ", "type": "種類", "modified": "更新日時",
        "confirm_delete": "選択した項目を削除しますか？", "confirm_overwrite": "同名の項目があります。上書きしますか？",
        "folder_name": "フォルダー名", "rename_prompt": "新しい名前", "file_operation_error": "ファイル操作に失敗しました: ",
    },
    "English": {
        "file": "File", "edit": "Edit", "view": "View", "tools": "Tools", "help": "Help",
        "settings": "Settings", "new": "New", "open": "Open…", "save": "Overwrite Save", "save_compile": "Save & Compile",
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
        "select_all": "Select All", "back": "Back", "forward": "Forward", "up": "Up", "refresh": "Refresh",
        "new_folder": "New Folder", "delete": "Delete", "rename": "Rename", "copy_path": "Copy Path",
        "size": "Size", "type": "Type", "modified": "Date Modified", "confirm_delete": "Delete the selected items?",
        "confirm_overwrite": "An item with the same name exists. Overwrite it?", "folder_name": "Folder name",
        "rename_prompt": "New name", "file_operation_error": "File operation failed: ",
    },
}
COLOR_KEYS = [
    "editor_background", "editor_foreground", "line_number_background", "line_number_foreground",
    "current_line_underline", "ruler_background", "ruler_foreground", "comment", "directive",
    "parameter", "macro", "number",
]

def _safe_int(config, section, option, fallback, minimum=None, maximum=None):
    try:
        value = config.getint(section, option, fallback=fallback)
    except (ValueError, configparser.Error):
        value = fallback
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _safe_bool(config, section, option, fallback):
    try:
        return config.getboolean(section, option, fallback=fallback)
    except (ValueError, configparser.Error):
        return fallback


def read_config():
    config = configparser.ConfigParser()
    existing_configs = [p for p in (CONFIG_PATH, APPDATA_CONFIG_PATH) if p.exists()]
    config_path = max(existing_configs, key=lambda p: p.stat().st_mtime) if existing_configs else CONFIG_PATH
    if config_path.exists():
        try:
            config.read(config_path, encoding="utf-8")
        except (OSError, configparser.Error):
            pass
    values = {
        "language": config.get("General", "language", fallback=DEFAULTS["language"]),
        "compiler_path": config.get("General", "compiler_path", fallback=DEFAULTS["compiler_path"]),
        "explorer_path": config.get("General", "explorer_path", fallback=str(Path.cwd())),
        "theme": config.get("Appearance", "theme", fallback=DEFAULTS["theme"]),
        "font_size": _safe_int(config, "Appearance", "font_size", int(DEFAULTS["font_size"]), 7, 36),
        "show_line_numbers": _safe_bool(config, "Appearance", "show_line_numbers", True),
        "show_ruler": _safe_bool(config, "Appearance", "show_ruler", True),
        "show_current_line_underline": _safe_bool(config, "Appearance", "show_current_line_underline", True),
        "window_geometry": config.get("Window", "geometry", fallback=""),
        "window_state": config.get("Window", "state", fallback=""),
        "explorer_width": _safe_int(config, "Window", "explorer_width", 280, 160, 1200),
        "output_height": _safe_int(config, "Window", "output_height", 180, 80, 900),
        "explorer_sort_column": _safe_int(config, "Explorer", "sort_column", 0, 0, 3),
        "explorer_sort_order": config.get("Explorer", "sort_order", fallback="ascending"),
        "explorer_column_widths": [
            _safe_int(config, "Explorer", f"column_width_{i}", default, 40, 2000)
            for i, default in enumerate((190, 85, 100, 160))
        ],
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
        "explorer_path": str(values.get("explorer_path", Path.cwd())),
    }
    config["Appearance"] = {
        "theme": str(values["theme"]),
        "font_size": str(values["font_size"]),
        "show_line_numbers": str(values["show_line_numbers"]).lower(),
        "show_ruler": str(values["show_ruler"]).lower(),
        "show_current_line_underline": str(values["show_current_line_underline"]).lower(),
    }
    config["Colors"] = {key: str(values["colors"].get(key, DEFAULTS["colors"][key])) for key in COLOR_KEYS}
    config["Window"] = {
        "geometry": str(values.get("window_geometry", "")),
        "state": str(values.get("window_state", "")),
        "explorer_width": str(values.get("explorer_width", 280)),
        "output_height": str(values.get("output_height", 180)),
    }
    config["Explorer"] = {
        "sort_column": str(values.get("explorer_sort_column", 0)),
        "sort_order": str(values.get("explorer_sort_order", "ascending")),
    }
    for i, width in enumerate(values.get("explorer_column_widths", [190, 85, 100, 160])):
        config["Explorer"][f"column_width_{i}"] = str(width)
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w", encoding="utf-8") as stream:
            config.write(stream)
        return CONFIG_PATH
    except OSError:
        # Executables installed in protected folders (e.g. Program Files) cannot
        # write beside themselves; persist settings in the user's roaming profile.
        APPDATA_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with APPDATA_CONFIG_PATH.open("w", encoding="utf-8") as stream:
            config.write(stream)
        return APPDATA_CONFIG_PATH

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
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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
        self.setCentralWidget(self.editor)

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
        self.action_find.setText(self.tr("find"))
        self.back_button.setToolTip(self.tr("back"))
        self.forward_button.setToolTip(self.tr("forward"))
        self.up_button.setToolTip(self.tr("up"))
        self.refresh_button.setToolTip(self.tr("refresh"))
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
        event.accept()

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
