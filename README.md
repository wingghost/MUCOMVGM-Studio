# MUCOMVGM Studio (MVS)

Windows-oriented MML authoring IDE for the MUCOMVGM compiler.

## Run (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python mucomvgm-studio.py
```

Use **Settings / 設定** to choose the UI language, editor theme, font size, display options, syntax colors, and `mucomvgm.exe` path. Settings are saved to `mucomvgm-studio.ini` beside the application script. The INI file is generated at runtime and intentionally ignored by Git.

## Current features in this working draft

- Japanese and English UI with immediate language switching from Settings.
- Light, dark, system and custom theme selection.
- Configurable editor font size; Ctrl+mouse wheel zooms in/out.
- Line-number gutter, current-line underline, and a ruler marked every 10 columns.
- Lightweight syntax highlighting for comments, directives, command/parameter tokens, macros and numeric values; note letters are intentionally not specially colored.
- Find dialog (Ctrl+F), next (F3), previous (Shift+F3).
- Compiler executable path setting and compile output panel.
- Settings persisted to `mucomvgm-studio.ini`.

## Important notes

This is a working draft, not yet verified end-to-end on Windows with a real MUCOMVGM compiler. The highlighter is heuristic and should be refined against actual MUCOMVGM MML syntax examples. Compilation is delegated to `mucomvgm.exe`, which is not bundled here.
