from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QSettings, QSize
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QTextCharFormat, QSyntaxHighlighter, QTextFormat
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDockWidget, QFileDialog, QFileSystemModel,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QStatusBar, QToolBar, QTreeView, QVBoxLayout, QWidget, QTabWidget,
)

APP_NAME = "MUCOMVGM Studio"
APP_ORG = "WINGGHOST"
BASE_DIR = Path(__file__).resolve().parent
LOCALES_DIR = BASE_DIR / "locales"

DEFAULT_TRANSLATIONS = {
    "Japanese": {
        "app_title": "MUCOMVGM Studio", "file": "ファイル", "edit": "編集", "view": "表示",
        "tools": "ツール", "help": "ヘルプ", "new": "新規作成", "open": "開く…",
        "save": "保存", "save_as": "名前を付けて保存…", "compile": "コンパイル",
        "open_folder": "フォルダーを開く…", "select_compiler": "コンパイラを選択…",
        "exit": "終了", "language": "言語 / Language", "explorer": "エクスプローラー",
        "output": "出力", "ready": "準備完了", "output_log": "コンパイルログ",
        "open_mml": "MMLファイルを開く", "mml_files": "MMLファイル (*.muc *.mml);;すべてのファイル (*)",
        "save_mml": "MMLファイルを保存", "save_filter": "MMLファイル (*.muc);;すべてのファイル (*)",
        "untitled": "無題.muc", "unsaved": "未保存の変更があります。保存しますか？",
        "confirm_exit": "終了しますか？", "compile_start": "コンパイル開始: ",
        "compile_success": "コンパイル成功: ", "compile_failed": "コンパイル失敗 (終了コード: ",
        "compiler_missing": "mucomvgm.exe が見つかりません。ツールメニューから指定してください。",
        "select_compiler_title": "mucomvgm.exe を選択", "compiler_filter": "実行ファイル (*.exe);;すべてのファイル (*)",
        "compile_error": "コンパイルを開始できませんでした: ", "saved": "保存しました: ",
        "language_changed": "言語設定を変更しました。", "line_col": "行 {line}, 列 {col}",
        "no_file": "ファイルが開かれていません", "no_output": "想定されたVGMファイルが見つかりません: ",
        "new_file": "新規MML", "about": "MUCOMVGM Studio（MVS）試作版\n既存の mucomvgm.exe を呼び出してコンパイルします。",
        "about_title": "このアプリについて", "browse": "参照…", "compiler_path": "コンパイラのパス",
        "cancel": "キャンセル", "ok": "OK", "save_failed": "保存できませんでした: ",
        "save_before_compile": "コンパイル前にMMLを保存します。", "compile_running": "コンパイル中…",
        "clear_output": "ログをクリア", "undo": "元に戻す", "redo": "やり直し",
        "cut": "切り取り", "copy": "コピー", "paste": "貼り付け",
    },
    "English": {
        "app_title": "MUCOMVGM Studio", "file": "File", "edit": "Edit", "view": "View",
        "tools": "Tools", "help": "Help", "new": "New", "open": "Open…", "save": "Save",
        "save_as": "Save As…", "compile": "Compile", "open_folder": "Open Folder…",
        "select_compiler": "Select Compiler…", "exit": "Exit", "language": "Language / 言語",
        "explorer": "Explorer", "output": "Output", "ready": "Ready", "output_log": "Compile Log",
        "open_mml": "Open MML File", "mml_files": "MML files (*.muc *.mml);;All files (*)",
        "save_mml": "Save MML File", "save_filter": "MML files (*.muc);;All files (*)",
        "untitled": "Untitled.muc", "unsaved": "There are unsaved changes. Save them?",
        "confirm_exit": "Exit the application?", "compile_start": "Compiling: ",
        "compile_success": "Compile succeeded: ", "compile_failed": "Compile failed (exit code: ",
        "compiler_missing": "mucomvgm.exe was not found. Choose it from the Tools menu.",
        "select_compiler_title": "Select mucomvgm.exe", "compiler_filter": "Executable (*.exe);;All files (*)",
        "compile_error": "Could not start compiler: ", "saved": "Saved: ",
        "language_changed": "Language preference changed.", "line_col": "Line {line}, Col {col}",
        "no_file": "No file is open", "no_output": "Expected VGM output was not found: ",
        "new_file": "New MML", "about": "MUCOMVGM Studio (MVS) prototype\nCompilation is delegated to the existing mucomvgm.exe.",
        "about_title": "About", "browse": "Browse…", "compiler_path": "Compiler path",
        "cancel": "Cancel", "ok": "OK", "save_failed": "Could not save file: ",
        "save_before_compile": "The MML file will be saved before compilation.", "compile_running": "Compiling…",
        "clear_output": "Clear Log", "undo": "Undo", "redo": "Redo", "cut": "Cut", "copy": "Copy", "paste": "Paste",
    },
}

def load_translations():
    translations = {name: values.copy() for name, values in DEFAULT_TRANSLATIONS.items()}
    for path in LOCALES_DIR.glob("*.json"):
        try:
            translations[path.stem] = {**DEFAULT_TRANSLATIONS["Japanese"], **json.loads(path.read_text(encoding="utf-8"))}
        except (OSError, json.JSONDecodeError):
            pass
    return translations

class MmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = [
            (r";.*$", "#6A9955"),
            (r"#(?:voice|pcm|pcmlist)\b", "#C586C0"),
            (r"\b(?:EX\d+|[cdefgabCDEFGAB])\b", "#4FC1FF"),
            (r"\b(?:[tT][+-]?\d+|[oO]\d+|[lL]\d+|[vV]\d+|[qQ]\d+|[rR])\b", "#DCDCAA"),
            (r"@[A-Za-z0-9%]*", "#D7BA7D"),
        ]
        import re
        self.rules = [(re.compile(pattern), color) for pattern, color in self.rules]

    def highlightBlock(self, text):
        for pattern, color in self.rules:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

class MmlEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = MmlHighlighter(self.document())
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translations = load_translations()
        self.settings = QSettings(APP_ORG, APP_NAME)
        self.language = self.settings.value("language", "Japanese")
        if self.language not in self.translations:
            self.language = "Japanese"
        self.current_file: Path | None = None
        self.project_root = Path.cwd()
        self.compiler_path = Path(self.settings.value("compiler_path", str(BASE_DIR / "mucomvgm.exe")))
        self.process: QProcess | None = None
        self._build_ui()
        self.retranslate()
        self.new_file()
        self.resize(1200, 780)

    def tr(self, key):
        return self.translations[self.language].get(key, self.translations["Japanese"].get(key, key))

    def _build_ui(self):
        self.editor = MmlEditor()
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
        self.output_dock.setMinimumHeight(150)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.actions = {}
        for key, callback in (("new", self.new_file), ("open", self.open_file), ("save", self.save_file), ("compile", self.compile_file)):
            action = QAction(self)
            action.triggered.connect(callback)
            toolbar.addAction(action)
            self.actions[key] = action
        self.language_combo = QComboBox()
        self.language_combo.addItems(self.translations.keys())
        self.language_combo.setCurrentText(self.language)
        self.language_combo.currentTextChanged.connect(self.change_language)
        toolbar.addWidget(QLabel("  "))
        toolbar.addWidget(self.language_combo)

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
        for key, callback in (("undo", self.editor.undo), ("redo", self.editor.redo), ("cut", self.editor.cut), ("copy", self.editor.copy), ("paste", self.editor.paste)):
            action = QAction(self)
            action.triggered.connect(callback)
            self.menu_edit.addAction(action)
            self.actions[key] = action
        self.menu_view.addAction(self.explorer_dock.toggleViewAction())
        self.menu_view.addAction(self.output_dock.toggleViewAction())
        self.action_select_compiler = QAction(self)
        self.action_select_compiler.triggered.connect(self.select_compiler)
        self.menu_tools.addAction(self.action_select_compiler)
        self.action_clear_output = QAction(self)
        self.action_clear_output.triggered.connect(self.output_log.clear)
        self.menu_tools.addAction(self.action_clear_output)
        self.action_about = QAction(self)
        self.action_about.triggered.connect(lambda: QMessageBox.about(self, self.tr("about_title"), self.tr("about")))
        self.menu_help.addAction(self.action_about)

    def retranslate(self):
        self.setWindowTitle(self.tr("app_title"))
        for menu, key in ((self.menu_file, "file"), (self.menu_edit, "edit"), (self.menu_view, "view"), (self.menu_tools, "tools"), (self.menu_help, "help")):
            menu.setTitle(self.tr(key))
        for key, action in self.actions.items():
            action.setText(self.tr(key))
        self.action_save_as.setText(self.tr("save_as"))
        self.action_open_folder.setText(self.tr("open_folder"))
        self.action_exit.setText(self.tr("exit"))
        self.action_select_compiler.setText(self.tr("select_compiler"))
        self.action_clear_output.setText(self.tr("clear_output"))
        self.action_about.setText(self.tr("about_title"))
        self.explorer_dock.setWindowTitle(self.tr("explorer"))
        self.output_dock.setWindowTitle(self.tr("output"))
        self.status_label.setText(self.tr("ready"))
        self.update_cursor_status()
        self.update_title()

    def change_language(self, language):
        if language in self.translations and language != self.language:
            self.language = language
            self.settings.setValue("language", language)
            self.retranslate()
            self.status_label.setText(self.tr("language_changed"))

    def update_title(self, *_):
        name = self.current_file.name if self.current_file else self.tr("untitled")
        dirty = " *" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{dirty} — {self.tr('app_title')}")

    def update_cursor_status(self):
        cursor = self.editor.textCursor()
        self.cursor_label.setText(self.tr("line_col").format(line=cursor.blockNumber() + 1, col=cursor.positionInBlock() + 1))

    def log(self, message):
        self.output_log.appendPlainText(message)

    def confirm_save_if_dirty(self):
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(self, self.tr("app_title"), self.tr("unsaved"),
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
            QMessageBox.critical(self, self.tr("app_title"), str(exc))
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
            QMessageBox.critical(self, self.tr("app_title"), self.tr("save_failed") + str(exc))
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

    def select_compiler(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("select_compiler_title"), str(self.compiler_path), self.tr("compiler_filter"))
        if path:
            self.compiler_path = Path(path)
            self.settings.setValue("compiler_path", str(self.compiler_path))
            self.status_label.setText(str(self.compiler_path))

    def compile_file(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.log(self.tr("compile_running"))
            return
        if not self.save_file() or self.current_file is None:
            return
        compiler = self.compiler_path
        candidates = [self.current_file.parent / "mucomvgm.exe", BASE_DIR / "mucomvgm.exe"]
        if not compiler.is_file():
            compiler = next((p for p in candidates if p.is_file()), compiler)
        if not compiler.is_file():
            QMessageBox.warning(self, self.tr("app_title"), self.tr("compiler_missing"))
            return
        self.log("\n" + "=" * 60)
        self.log(self.tr("compile_start") + f'"{compiler}" "{self.current_file.name}"')
        self.log(self.tr("save_before_compile"))
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
            text = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace").rstrip()
            if text:
                self.log(text)

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
