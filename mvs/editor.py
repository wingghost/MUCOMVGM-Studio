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

from .config import DEFAULTS

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
        self.textChanged.connect(self.update_extra_selections)
        self.search_highlight_term = ""
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
        # QPlainTextEdit draws its active text selection using QPalette.Highlight.
        # Set that role to the user-configured search color while a search/replace
        # target is active, so the current single match is visibly colored even on
        # platforms where QTextEdit.ExtraSelection is visually overridden by the
        # native selection palette.
        if getattr(self, "search_highlight_term", ""):
            palette.setColor(palette.ColorRole.Highlight, QColor(colors.get("search_match", "#FF9F1C")))
            palette.setColor(palette.ColorRole.HighlightedText, QColor("#202020"))
        else:
            app_palette = QApplication.palette()
            palette.setColor(palette.ColorRole.Highlight, app_palette.color(app_palette.ColorRole.Highlight))
            palette.setColor(palette.ColorRole.HighlightedText, app_palette.color(app_palette.ColorRole.HighlightedText))
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

    def set_search_highlight(self, term):
        """Color only the active search/replace selection using the Settings color."""
        self.search_highlight_term = term or ""
        palette = self.palette()
        if self.search_highlight_term:
            color = self.settings_getter().get("colors", {}).get("search_match", "#FF9F1C")
            palette.setColor(palette.ColorRole.Highlight, QColor(color))
            palette.setColor(palette.ColorRole.HighlightedText, QColor("#202020"))
        else:
            app_palette = QApplication.palette()
            palette.setColor(palette.ColorRole.Highlight, app_palette.color(app_palette.ColorRole.Highlight))
            palette.setColor(palette.ColorRole.HighlightedText, app_palette.color(app_palette.ColorRole.HighlightedText))
        self.setPalette(palette)
        self.update_extra_selections()

    def update_extra_selections(self, *_):
        selections = []
        term = getattr(self, "search_highlight_term", "")
        cursor = self.textCursor()
        # Show exactly one highlight: only when the editor selection is the current
        # search match. Never color every occurrence in the document.
        if term and cursor.hasSelection() and cursor.selectedText() == term:
            extra = QTextEdit.ExtraSelection()
            extra.cursor = QTextCursor(cursor)
            fmt = QTextCharFormat()
            colors = self.settings_getter().get("colors", {})
            fmt.setBackground(QColor(colors.get("search_match", "#FF9F1C")))
            fmt.setForeground(QColor("#202020"))
            extra.format = fmt
            selections.append(extra)

        # The full-width underline is painted by CurrentLineOverlay, including on blank lines.
        self.setExtraSelections(selections)