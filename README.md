# MUCOMVGM Studio (MVS)

MUCOMVGM Studio is a Windows-oriented MML authoring GUI for the [MUCOMVGM](https://github.com/wingghost/MUCOMVGM) compiler.

> **Status: prototype.** This is an early starting point for development, not a release-ready IDE. Windows GUI startup and real compiler execution still need to be verified.

## Current prototype features

- VS Code-inspired layout with a file explorer, central MML editor, and compile log.
- Open and save `.muc` / `.mml` files (UTF-8 with CP932 fallback when opening).
- Basic MML syntax highlighting.
- Compile through the existing `mucomvgm.exe` command-line program.
- Japanese default UI and English selectable from the toolbar.
- JSON locale packs for adding further languages.
- Selectable compiler path.

## Run from source (Windows)

1. Install Python 3.10 or later.
2. Open a terminal in the repository directory.
3. Install dependencies and start MVS:

   ```powershell
   py -m pip install -r requirements.txt
   py mucomvgm_studio.py
   ```

4. Put `mucomvgm.exe` beside the MVS script or beside the MML file, or select the executable from **Tools → Select Compiler**.
5. Open an MML file and press **Compile**. The compiler runs with the MML file's directory as its working directory so relative voice/PCM assets can be found.

## Current limitations

- The syntax highlighter is intentionally lightweight and does not validate the complete MML grammar.
- The GUI delegates compilation to `mucomvgm.exe`; the compiler is not bundled here.
- The prototype expects the compiler's default output filename to be the input MML basename with a `.vgm` extension.
- The UI and compiler integration have not yet been tested end-to-end on Windows.

## Project direction

MVS is maintained in a separate repository from MUCOMVGM so the GUI and compiler can evolve independently. The initial integration contract is the compiler CLI; future work can formalize error reporting and version compatibility.
