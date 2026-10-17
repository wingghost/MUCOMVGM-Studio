from __future__ import annotations

import configparser
import json
import os
import sys
from pathlib import Path

APP_NAME = "MUCOMVGM Studio"
APP_ORG = "WINGGHOST"
# In a PyInstaller one-file build, __file__ points into the temporary extraction
# directory. Use the executable directory for user-visible files instead.
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
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
        "search_match": "#FF9F1C",
    },
}
THEMES = {
    "Dark": {
        "editor_background": "#1E1E1E", "editor_foreground": "#D4D4D4",
        "line_number_background": "#252526", "line_number_foreground": "#858585",
        "current_line_underline": "#569CD6", "ruler_background": "#252526",
        "ruler_foreground": "#858585", "comment": "#6A9955",
        "directive": "#C586C0", "parameter": "#DCDCAA", "macro": "#D7BA7D",
        "number": "#B5CEA8", "search_match": "#FF9F1C",
    },
    "Light": {
        "editor_background": "#FFFFFF", "editor_foreground": "#202020",
        "line_number_background": "#F0F0F0", "line_number_foreground": "#777777",
        "current_line_underline": "#007ACC", "ruler_background": "#F0F0F0",
        "ruler_foreground": "#777777", "comment": "#008000",
        "directive": "#AF00DB", "parameter": "#795E26", "macro": "#A31515",
        "number": "#098658", "search_match": "#FFB000",
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
        "color_search_match": "検索対象の強調色",
        "apply": "適用", "ok": "OK", "cancel": "キャンセル", "find": "検索", "find_next": "次を検索",
        "find_previous": "前を検索", "find_text": "検索ワード", "replace": "置換", "replace_text": "置換ワード",
        "find_down": "下検索 (F3)", "replace_all": "全置換", "replace_count": "{count} 件を置換しました。", "not_found": "見つかりません: ",
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
        "color_search_match": "Search match highlight",
        "apply": "Apply", "ok": "OK", "cancel": "Cancel", "find": "Find", "find_next": "Find Next",
        "find_previous": "Find Previous", "find_text": "Search for", "replace": "Replace", "replace_text": "Replace with",
        "find_down": "Find Down (F3)", "replace_all": "Replace All", "replace_count": "Replaced {count} occurrence(s).", "not_found": "Not found: ",
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
    "parameter", "macro", "number", "search_match",
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

