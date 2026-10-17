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

from .config import APP_NAME, BASE_DIR

class PlayerMixin:
    """Playback/temporary-file lifecycle methods used by MainWindow."""

    def play_current_mml(self):
        """Compile the current editor buffer to an isolated hidden VGM and play it."""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.log(self.tr("compile_running"))
            return
        if self.player_compile_process and self.player_compile_process.state() != QProcess.ProcessState.NotRunning:
            self.stop_player(cleanup=True)
        else:
            self.stop_player(cleanup=True)

        work_dir = self.current_file.parent if self.current_file else self.project_root
        base_name = self.current_file.stem if self.current_file else "untitled"
        temp_source = work_dir / f".{base_name}.muc"
        temp_vgm = work_dir / f".{base_name}.vgm"
        # Never overwrite or later delete hidden files that were not created by this player.
        collisions = [path for path in (temp_source, temp_vgm) if path.exists()]
        if collisions:
            paths = "\n".join(str(path) for path in collisions)
            message = ("一時再生ファイルと同名のファイルが既に存在します。上書きせず再生を中止します。\n" + paths
                       if self.language == "Japanese" else
                       "A playback temp file already exists. Playback was cancelled without overwriting it.\n" + paths)
            QMessageBox.warning(self, APP_NAME, message)
            return

        compiler = Path(self.values.get("compiler_path", str(BASE_DIR / "mucomvgm.exe"))).expanduser()
        candidates = [work_dir / "mucomvgm.exe", BASE_DIR / "mucomvgm.exe"]
        if not compiler.is_file():
            compiler = next((candidate for candidate in candidates if candidate.is_file()), compiler)
        if not compiler.is_file():
            QMessageBox.warning(self, APP_NAME, self.tr("compiler_missing"))
            return
        mml_text = self.editor.toPlainText()
        if hasattr(self, "visualizer"):
            self.visualizer.configure_from_mml(mml_text)
        try:
            temp_source.write_text(mml_text, encoding="utf-8", newline="\n")
        except OSError as exc:
            QMessageBox.critical(self, APP_NAME, str(exc))
            return

        self._player_temp_source = temp_source
        self._player_temp_vgm = temp_vgm
        self._player_temp_files.update((temp_source, temp_vgm))
        self.log("\n" + "=" * 60)
        self.log(("一時ファイルをコンパイル: " if self.language == "Japanese" else "Compiling playback temp file: ") + str(temp_source))
        proc = QProcess(self)
        self.player_compile_process = proc
        proc.setWorkingDirectory(str(work_dir))
        proc.setProgram(str(compiler.resolve()))
        proc.setArguments([temp_source.name])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read_player_process_output(p))
        proc.finished.connect(lambda code, status, p=proc: self._player_compile_finished(p, code, status))
        proc.errorOccurred.connect(lambda error, p=proc: self._player_process_error(p, error, compiling=True))
        proc.start()
        self.player_status_label.setText("コンパイル中…" if self.language == "Japanese" else "Compiling…")


    def _read_player_process_output(self, proc: QProcess):
        output = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace").rstrip()
        if output:
            self.log(output)


    def _player_compile_finished(self, proc: QProcess, exit_code: int, exit_status):
        self._read_player_process_output(proc)
        if self.player_compile_process is proc:
            self.player_compile_process = None
        proc.deleteLater()
        if exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            self.log(("プレイヤー用コンパイルに失敗しました。" if self.language == "Japanese" else "Playback compilation failed."))
            self.player_status_label.setText("コンパイル失敗" if self.language == "Japanese" else "Compile failed")
            self._cleanup_player_temp_files()
            return
        vgm_path = self._player_temp_vgm
        if not vgm_path or not vgm_path.is_file():
            self.log(("一時VGMファイルが生成されませんでした。" if self.language == "Japanese" else "The temporary VGM was not created."))
            self.player_status_label.setText("再生できません" if self.language == "Japanese" else "Cannot play")
            self._cleanup_player_temp_files()
            return
        player_candidates = [BASE_DIR / "libvgm" / "player.exe", vgm_path.parent / "libvgm" / "player.exe"]
        player_exe = next((candidate for candidate in player_candidates if candidate.is_file()), None)
        if player_exe is None:
            self.log(("libvgm\\player.exe が見つかりません。" if self.language == "Japanese" else "libvgm\\player.exe was not found."))
            self.player_status_label.setText("プレイヤー未検出" if self.language == "Japanese" else "Player not found")
            self._cleanup_player_temp_files()
            return
        proc = QProcess(self)
        self.player_process = proc
        if hasattr(self, "visualizer"):
            self.visualizer.load_vgm(vgm_path)
        proc.setWorkingDirectory(str(vgm_path.parent))
        proc.setProgram(str(player_exe.resolve()))
        proc.setArguments([str(vgm_path.resolve())])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read_player_process_output(p))
        proc.finished.connect(lambda _code, _status, p=proc: self._player_finished(p))
        proc.errorOccurred.connect(lambda error, p=proc: self._player_process_error(p, error, compiling=False))
        proc.start()
        if hasattr(self, "visualizer"):
            self.visualizer.start()
        self.player_status_label.setText("再生中" if self.language == "Japanese" else "Playing")
        self.log(("再生開始: " if self.language == "Japanese" else "Playing: ") + str(vgm_path))


    def _player_process_error(self, proc: QProcess, error, compiling: bool):
        prefix = ("プレイヤー用コンパイラーエラー: " if self.language == "Japanese" else "Playback compiler error: ") if compiling else ("libvgm起動エラー: " if self.language == "Japanese" else "libvgm launch error: ")
        self.log(prefix + proc.errorString())
        if error == QProcess.ProcessError.FailedToStart:
            attr = "player_compile_process" if compiling else "player_process"
            if getattr(self, attr, None) is proc:
                setattr(self, attr, None)
            proc.deleteLater()
            self.player_status_label.setText("起動失敗" if self.language == "Japanese" else "Failed to start")
            self._cleanup_player_temp_files()


    def _player_finished(self, proc: QProcess):
        self._read_player_process_output(proc)
        if self.player_process is proc:
            self.player_process = None
        proc.deleteLater()
        self.player_status_label.setText("停止中" if self.language == "Japanese" else "Stopped")
        if hasattr(self, "visualizer"):
            self.visualizer.stop()
        self._cleanup_player_temp_files()


    def stop_player(self, cleanup=True):
        for attr in ("player_process", "player_compile_process"):
            proc = getattr(self, attr, None)
            if proc is not None:
                if proc.state() != QProcess.ProcessState.NotRunning:
                    proc.kill()
                    proc.waitForFinished(1500)
                self._read_player_process_output(proc)
                proc.deleteLater()
                setattr(self, attr, None)
        if hasattr(self, "visualizer"):
            self.visualizer.stop()
        if cleanup:
            self._cleanup_player_temp_files()
        if hasattr(self, "player_status_label"):
            self.player_status_label.setText("停止中" if self.language == "Japanese" else "Stopped")


    def _cleanup_player_temp_files(self):
        for path in tuple(self._player_temp_files):
            try:
                if path.exists() and path.is_file():
                    path.unlink()
            except OSError as exc:
                self.log(("一時ファイルを削除できませんでした: " if self.language == "Japanese" else "Could not remove temp file: ") + f"{path}: {exc}")
            else:
                self._player_temp_files.discard(path)
        if self._player_temp_source not in self._player_temp_files:
            self._player_temp_source = None
        if self._player_temp_vgm not in self._player_temp_files:
            self._player_temp_vgm = None

