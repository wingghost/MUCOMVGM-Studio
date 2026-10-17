from __future__ import annotations

import math
import struct
import re
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy


@dataclass
class VgmEvent:
    sample: int
    chip: str
    port: int
    reg: int
    value: int
    instance: int = 1


_CHIP_NAME_RE = re.compile(
    r"\s*#chip(?:\s+(\d+))?\s+([A-Za-z][A-Za-z0-9_+-]*)",
    re.IGNORECASE,
)
_KNOWN_CHIPS = {"YM2608", "OPNA", "YM2151", "OPM"}
_CHIP_FAMILY = {
    "YM2608": ("YM2608", "OPNA"),
    "OPNA": ("YM2608", "OPNA"),
    "YM2151": ("YM2151", "OPM"),
    "OPM": ("YM2151", "OPM"),
}


class PianoRow(QWidget):
    """Realistic 8-octave piano keyboard; sounding notes are highlighted red."""
    LOW_NOTE = 24       # C1
    OCTAVES = 8
    WHITE_KEY_COUNT = OCTAVES * 7
    LABEL_W = 86
    WHITE_KEY_W = 8

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label = label
        self.notes: set[int] = set()
        self.meter = LevelMeter(self)
        self.level = 0.0
        self.setMinimumHeight(42)
        # Keep all eight octaves at a readable key width and let the scroll area scroll.
        self.setMinimumWidth(self.LABEL_W + self.WHITE_KEY_COUNT * self.WHITE_KEY_W + 22)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        return QSize(self.minimumWidth(), self.minimumHeight())

    def minimumSizeHint(self):
        return self.sizeHint()

    def set_notes(self, notes):
        self.notes = set(notes)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        label_w = self.LABEL_W
        top, bottom = 3, self.height() - 3
        key_h = bottom - top
        x0 = label_w
        key_w = self.WHITE_KEY_W
        black_pc = {1, 3, 6, 8, 10}
        white_pc = {0, 2, 4, 5, 7, 9, 11}

        p.setPen(self.palette().color(self.foregroundRole()))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        p.drawText(0, top, label_w - 8, key_h, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.label.replace("\n", "\n"))
        self.meter.move(self.width() - self.meter.width() - 2, (self.height() - self.meter.height()) // 2)

        # Draw the 56 white keys first, each with a distinct outline and subtle bottom edge.
        white_x = {}
        white_index = 0
        for midi in range(self.LOW_NOTE, self.LOW_NOTE + self.OCTAVES * 12):
            pc = midi % 12
            if pc not in white_pc:
                continue
            x = x0 + white_index * key_w
            white_x[midi] = x
            rect = (x, top, key_w, key_h)
            if midi in self.notes:
                fill = QColor("#e34242")
            else:
                fill = QColor("#fffdf7")
            p.setPen(QPen(QColor("#30343b"), 1))
            p.setBrush(fill)
            p.drawRoundedRect(x, top, key_w, key_h, 1.5, 1.5)
            # Small octave marker at each C key.
            if pc == 0:
                p.setPen(QColor("#626873"))
                p.setFont(QFont("Segoe UI", 6))
                p.drawText(x, bottom - 14, key_w, 11, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, f"C{midi // 12 - 1}")
            white_index += 1

        # Black keys overlap the white keys, as on a real piano.
        black_w = max(4, int(key_w * 0.60))
        black_h = int(key_h * 0.61)
        for midi in range(self.LOW_NOTE, self.LOW_NOTE + self.OCTAVES * 12):
            pc = midi % 12
            if pc not in black_pc:
                continue
            # Locate the white key immediately to the left of this black key.
            left_white = midi - 1
            while left_white >= self.LOW_NOTE and left_white not in white_x:
                left_white -= 1
            if left_white not in white_x:
                continue
            x = white_x[left_white] + key_w - black_w // 2
            active = midi in self.notes
            p.setPen(QPen(QColor("#17191e"), 1))
            p.setBrush(QColor("#e34242") if active else QColor("#242830"))
            p.drawRoundedRect(x, top, black_w, black_h, 2, 2)
            if active:
                p.setPen(QColor("#ffffff"))
                p.setFont(QFont("Segoe UI", 6, QFont.Weight.Bold))
                p.drawText(x, top + 2, black_w, black_h - 3, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, "●")


class LevelMeter(QWidget):
    """Compact vertical event-level meter (estimated from carrier TL, not PCM)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = 0.0
        self.setFixedSize(13, 34)

    def set_level(self, level):
        level = max(0.0, min(1.0, float(level)))
        if abs(self.level - level) > 0.005:
            self.level = level
            self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor("#343b46"), 1))
        p.setBrush(QColor("#171c24"))
        p.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 3, 3)
        inner_h = self.height() - 6
        lit_h = int(inner_h * self.level)
        if lit_h:
            color = QColor("#e65a5a") if self.level > .85 else QColor("#43d6a3")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(3, self.height()-3-lit_h, self.width()-6, lit_h, 2, 2)


class RhythmStrip(QWidget):
    """Six compact, finely graduated activity meters for YM2608 rhythm voices."""
    NAMES = (("BD", 0), ("SD", 1), ("TOP", 2), ("HH", 3), ("TOM", 4), ("RIM", 5))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.levels = [0.0] * 6
        self.peaks = [0.0] * 6
        self.setMinimumHeight(42)
        self.setMaximumHeight(42)
        self.setMinimumWidth(PianoRow.LABEL_W + PianoRow.WHITE_KEY_COUNT * PianoRow.WHITE_KEY_W + 22)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def trigger(self, instrument: int):
        if 0 <= instrument < 6:
            self.levels[instrument] = 1.0
            self.peaks[instrument] = 1.0
            self.update()

    def tick(self):
        changed = False
        for i in range(6):
            old = self.levels[i]
            self.levels[i] = max(0.0, old - 0.035)
            self.peaks[i] = max(self.levels[i], self.peaks[i] - 0.012)
            changed |= old != self.levels[i]
        if changed:
            self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        label_w = PianoRow.LABEL_W
        p.setPen(self.palette().color(self.foregroundRole()))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        p.drawText(0, 3, label_w - 8, self.height() - 6, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "YM2608\nRhythm")
        margin, gap = label_w + 3, 4
        available = max(6, self.width() - margin - 3)
        cell_w = max(1, (available - gap * 5) // 6)
        for i, (name, _) in enumerate(self.NAMES):
            x = margin + i * (cell_w + gap)
            p.setPen(QColor("#aeb7c4"))
            p.setFont(QFont("Segoe UI", 6, QFont.Weight.DemiBold))
            p.drawText(x, 2, cell_w, 11, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, name)
            bx, by, bw, bh = x, 15, cell_w, 11
            p.setPen(QPen(QColor("#343b46"), 1))
            p.setBrush(QColor("#171c24"))
            p.drawRoundedRect(bx, by, bw, bh, 3, 3)
            inner_x, inner_y, inner_w, inner_h = bx + 2, by + 2, bw - 4, bh - 4
            lit_w = int(inner_w * self.levels[i])
            if lit_w > 0:
                # Smooth fill with a warm peak region, without pretending to be PCM dB.
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor("#43d6a3"))
                p.drawRoundedRect(inner_x, inner_y, lit_w, inner_h, 2, 2)
                if lit_w > inner_w * 0.72:
                    p.setBrush(QColor("#f0c35a"))
                    p.drawRoundedRect(inner_x + int(inner_w * 0.72), inner_y,
                                      max(0, lit_w - int(inner_w * 0.72)), inner_h, 2, 2)
            peak_x = inner_x + int(inner_w * self.peaks[i])
            if self.peaks[i] > 0.02:
                p.setPen(QPen(QColor("#f5f7fa"), 2))
                p.drawLine(peak_x, by + 1, peak_x, by + bh - 1)


class VgmVisualizer(QWidget):
    """VGM register-stream visualizer. It displays event activity, not PCM loudness."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events: list[VgmEvent] = []
        self.event_index = 0
        self.elapsed = QElapsedTimer()
        self.rows: dict[tuple[str, str, int], PianoRow] = {}
        self.active: dict[tuple[str, str, int], set[int]] = {}
        self.chip_declarations: list[str] = []
        self.rhythm = RhythmStrip()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)
        title = QLabel("発音モニター / Note Activity")
        title.setStyleSheet("font-weight: bold")
        layout.addWidget(title)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.rows_host = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(3)
        self.scroll.setWidget(self.rows_host)
        layout.addWidget(self.scroll, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self._advance)
        self._sample_rate = 44100
        self._total_samples = 0
        self.chip_declarations = ["YM2608"]
        self._build_rows([])

    def configure_from_mml(self, mml_text: str):
        """Configure visible chip rows from the MML #chip declarations."""
        found = []
        for line in mml_text.splitlines():
            match = _CHIP_NAME_RE.match(line)
            if not match:
                continue
            name = match.group(2).upper()
            if name in _KNOWN_CHIPS:
                found.append(name)
        if not found:
            found = ["YM2608"]
        if found != self.chip_declarations:
            self.chip_declarations = found
            self._build_rows([])

    @staticmethod
    def _u32(data: bytes, offset: int) -> int:
        return struct.unpack_from('<I', data, offset)[0] if offset + 4 <= len(data) else 0

    def load_vgm(self, path):
        try:
            data = open(path, 'rb').read()
        except OSError:
            self.events = []
            return
        if len(data) < 0x40 or data[:4] != b'Vgm ':
            self.events = []
            return
        version = self._u32(data, 8)
        offset = 0x40
        rel = self._u32(data, 0x34) if version >= 0x150 and len(data) >= 0x38 else 0
        if rel:
            offset = 0x34 + rel
        sample = 0
        events = []
        while offset < len(data):
            cmd = data[offset]
            offset += 1
            if cmd == 0x66:
                break
            if cmd == 0x61 and offset + 2 <= len(data):
                sample += data[offset] | (data[offset + 1] << 8); offset += 2
            elif cmd == 0x62:
                sample += 735
            elif cmd == 0x63:
                sample += 882
            elif 0x70 <= cmd <= 0x8F:
                if cmd <= 0x7F:
                    sample += (cmd & 0x0F) + 1
                else:
                    sample += cmd & 0x0F
                    offset += 1  # YM2612 DAC write byte accompanying the wait
            elif cmd in (0x56, 0x57, 0xA6, 0xA7, 0x54, 0xA4) and offset + 2 <= len(data):
                reg, value = data[offset], data[offset + 1]; offset += 2
                if cmd in (0x54, 0xA4):
                    events.append(VgmEvent(sample, "YM2151", 0, reg, value, 1 if cmd == 0x54 else 2))
                else:
                    port = 0 if cmd in (0x56, 0xA6) else 1
                    instance = 1 if cmd in (0x56, 0x57) else 2
                    events.append(VgmEvent(sample, "YM2608", port, reg, value, instance))
            elif cmd == 0x67 and offset + 6 <= len(data):
                # VGM data block: 66, type, size(4), payload
                if data[offset] == 0x66:
                    size = self._u32(data, offset + 2)
                    offset += 6 + size
                else:
                    break
            elif cmd in (0x4F, 0x50):
                offset += 1
            elif cmd in (0x51, 0x52, 0x53, 0x55, 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F):
                offset += 2
            elif cmd in (0xA0, 0xB0):
                offset += 2
            elif cmd in (0xC0, 0xC1, 0xC2, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4):
                offset += 3
            elif cmd == 0xE0:
                offset += 4
            elif cmd == 0x90:
                offset += 4
            elif cmd == 0x91:
                offset += 4
            elif cmd == 0x92:
                offset += 5
            elif cmd == 0x93:
                offset += 10
            elif cmd == 0x94:
                offset += 1
            elif cmd == 0x95:
                offset += 4
            elif cmd in (0x30, 0x3F):
                offset += 1
            elif 0xA1 <= cmd <= 0xBF or 0xC3 <= cmd <= 0xCF or 0xD5 <= cmd <= 0xDF:
                offset += 2
            else:
                # Unknown command; stop instead of risking a desynchronized parse.
                break
        self.events = events
        self._total_samples = sample
        # Keep the keyboard widgets stable during playback. Rebuilding them
        # here caused the visible keyboard to vanish when the VGM was loaded.

    def _build_rows(self, events):
        # Rebuild only when the source's #chip declarations change, never on playback ticks.
        # IMPORTANT: self.rhythm is a persistent widget. Do not deleteLater() it here:
        # this method reuses that same instance when adding the rhythm strip back.
        for i in reversed(range(self.rows_layout.count())):
            item = self.rows_layout.takeAt(i)
            widget = item.widget()
            if widget is not None:
                self.rows_layout.removeWidget(widget)
                if widget is self.rhythm:
                    widget.hide()
                    continue
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.rows.clear()
        self.active.clear()
        declarations = self.chip_declarations or ["YM2608"]
        counts = {}
        ordered = []
        for chip_name in declarations:
            counts[chip_name] = counts.get(chip_name, 0) + 1
            instance = counts[chip_name]
            display = chip_name if counts[chip_name] == 1 else f"{chip_name} #{instance}"
            if chip_name in ("YM2608", "OPNA"):
                ordered.extend((f"{chip_name}@{instance}", display, "FM", i) for i in range(6))
                ordered.extend((f"{chip_name}@{instance}", display, "SSG", i) for i in range(3))
                ordered.append((f"{chip_name}@{instance}", display, "ADPCM", 0))
                ordered.extend((f"{chip_name}@{instance}", display, "EFFECT", i) for i in range(3))
                # Rhythm meter is added once below all keyboard rows.
            elif chip_name in ("YM2151", "OPM"):
                ordered.extend((f"{chip_name}@{instance}", display, "FM", i) for i in range(8))
        for key_chip, display, kind, channel in ordered:
            if kind == "EFFECT":
                effect_name = ("L", "M", "N")[channel]
                row_label = f"{display}\nFM3-{channel + 2}"
            else:
                row_label = f"{display}\n{kind} {channel + 1}"
            row = PianoRow(row_label)
            key = (key_chip, kind, channel)
            self.rows[key] = row
            self.active[key] = set()
            self.rows_layout.addWidget(row)
        if any(name in ("YM2608", "OPNA") for name in declarations):
            self.rhythm.show()
            self.rows_layout.addWidget(self.rhythm)
        self.rows_layout.addStretch(1)
        row_width = max((row.minimumWidth() for row in self.rows.values()), default=900)
        self.rows_layout.activate()
        content_size = self.rows_layout.sizeHint()
        fallback_h = max(42, len(self.rows) * 42 + 42)
        host_w = max(row_width, content_size.width(), 1)
        host_h = max(content_size.height(), fallback_h)
        self.rows_host.setMinimumWidth(host_w)
        self.rows_host.setMinimumHeight(host_h)
        self.rows_host.resize(host_w, host_h)
        self.rows_host.updateGeometry()
        self.scroll.widget().updateGeometry()
        self.scroll.updateGeometry()
        self.rows_host.update()
        self.scroll.viewport().update()
        QTimer.singleShot(0, self._refresh_scroll_geometry)

    def _refresh_scroll_geometry(self):
        if not self.rows_host or not self.scroll:
            return
        self.rows_layout.invalidate()
        self.rows_layout.activate()
        hint = self.rows_layout.sizeHint()
        fallback_h = max(42, len(self.rows) * 42 + 42)
        host_w = max(1, hint.width(), max((row.minimumWidth() for row in self.rows.values()), default=900))
        host_h = max(1, hint.height(), fallback_h)
        self.rows_host.setMinimumSize(host_w, host_h)
        self.rows_host.resize(host_w, host_h)
        self.rows_host.updateGeometry()
        self.scroll.widget().updateGeometry()
        self.scroll.viewport().update()
        self.rows_host.update()

    def start(self):
        self.event_index = 0
        for key in self.active:
            self.active[key].clear()
        for row in self.rows.values():
            row.set_notes(set())
            row.level = 0.0
            row.meter.set_level(0.0)
        self.rhythm.levels = [0] * 6
        self.elapsed.start()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        for key in self.active: self.active[key].clear()
        for row in self.rows.values():
            row.set_notes(set())
            row.level = 0.0
            row.meter.set_level(0.0)
        self.rhythm.levels = [0] * 6
        self.rhythm.update()

    def _advance(self):
        now_samples = self.elapsed.elapsed() * self._sample_rate // 1000
        while self.event_index < len(self.events) and self.events[self.event_index].sample <= now_samples:
            self._apply_event(self.events[self.event_index])
            self.event_index += 1
        self.rhythm.tick()
        for row in self.rows.values():
            if not row.notes:
                row.level = max(0.0, row.level - 0.018)
                row.meter.set_level(row.level)
        # libvgm can loop the VGM indefinitely. Keep replaying the parsed event
        # stream instead of stopping the visualizer after its first pass.
        if self.events and self._total_samples > 0 and now_samples >= self._total_samples:
            self.event_index = 0
            self.elapsed.restart()
            for key in self.active:
                self.active[key].clear()
            for row in self.rows.values():
                row.set_notes(set())
            self.rhythm.levels = [0.0] * 6
            self.rhythm.peaks = [0.0] * 6
            self.rhythm.update()

    def _resolve_key(self, chip: str, kind: str, channel: int, instance: int):
        names = _CHIP_FAMILY.get(chip, (chip,))
        for name in names:
            key = (f"{name}@{instance}", kind, channel)
            if key in self.rows:
                return key
        for name in names:
            key = (f"{name}@1", kind, channel)
            if key in self.rows:
                return key
        return None

    def _set_row_notes(self, key, notes):
        if key is None or key not in self.rows:
            return
        self.active[key] = set(notes)
        self.rows[key].set_notes(self.active[key])
        if notes:
            self.rows[key].level = self._estimate_row_level(key)
            self.rows[key].meter.set_level(self.rows[key].level)

    def _estimate_row_level(self, key):
        """Estimate carrier loudness from most recently seen TL writes; 0..1."""
        tls = getattr(self, "_carrier_tl", {})
        values = tls.get(key, [])
        if not values:
            return 0.72
        attenuation = sum(values) / len(values)
        return max(0.06, min(1.0, 1.0 - attenuation / 127.0))

    def _track_tl(self, ev):
        # Keep TL values as per-channel estimates. FM channel/operator register
        # layouts differ by chip, so this is intentionally conservative.
        if ev.chip == "YM2608" and 0x40 <= ev.reg <= 0x4F:
            ch = ev.reg & 0x03
            if ch == 3:
                return
            ch += ((ev.reg >> 2) & 1) * 3
            key = self._resolve_key("YM2608", "FM", ch, ev.instance)
        elif ev.chip == "YM2151" and 0x60 <= ev.reg <= 0x7F:
            ch = ev.reg & 0x07
            key = self._resolve_key("YM2151", "FM", ch, ev.instance)
        else:
            return
        if key is not None:
            cache = getattr(self, "_carrier_tl", {})
            # TL is 7-bit; keep latest four operator values for a stable estimate.
            vals = cache.setdefault(key, [0, 0, 0, 0])
            op = (ev.reg >> 2) & 0x03
            vals[op] = ev.value & 0x7F
            self._carrier_tl = cache

    def _apply_event(self, ev: VgmEvent):
        self._track_tl(ev)
        inst = ev.instance
        # Track frequency/key-code registers before processing key-on events.
        if ev.chip == "YM2608" and ev.reg in (0xA0, 0xA1, 0xA2, 0xA4, 0xA5, 0xA6):
            channel = (ev.reg & 0x03) + (3 if ev.port == 1 else 0)
            cache = getattr(self, "_fnum2608_parts", {})
            low, high = cache.get((inst, channel), (0, 0))
            if ev.reg < 0xA4: low = ev.value
            else: high = ev.value
            cache[(inst, channel)] = (low, high)
            self._fnum2608_parts = cache
            self._fnum2608 = getattr(self, "_fnum2608", {})
            self._fnum2608[(inst, channel)] = (((high & 0x07) << 8) | low, (high >> 3) & 0x07)
        elif ev.chip == "YM2151" and 0x28 <= ev.reg <= 0x2F:
            channel = ev.reg - 0x28
            cache = getattr(self, "_fnum2151", {})
            keycode = ev.value
            semitone_map = {0: 0, 1: 1, 2: 2, 4: 3, 5: 4, 6: 5, 8: 6, 9: 7, 10: 8, 12: 9, 13: 10, 14: 11}
            octave = (keycode >> 4) & 0x07
            semitone = semitone_map.get(keycode & 0x0F, 0)
            cache[(inst, channel)] = (semitone, octave)
            self._fnum2151 = cache
        if ev.chip == "YM2608":
            if ev.port == 0 and ev.reg == 0x28:
                ch = ev.value & 0x03
                if ch == 3: return
                ch += ((ev.value >> 2) & 1) * 3
                key = self._resolve_key("YM2608", "FM", ch, inst)
                if key is None: return
                if ev.value & 0xF0:
                    note = self._fm_note_2608(inst, ch)
                    self._set_row_notes(key, {note} if note is not None else set())
                else:
                    self._set_row_notes(key, set())
            elif ev.port == 0 and 0x08 <= ev.reg <= 0x0A:
                ch = ev.reg - 0x08
                key = self._resolve_key("YM2608", "SSG", ch, inst)
                if key is None: return
                periods = getattr(self, "_ssg_period", {})
                period = periods.get((inst, ch), 0x100)
                note = max(0, min(127, round(69 + 12 * math.log2(max(1, 3579545 / (64 * max(1, period))) / 440))))
                self._set_row_notes(key, {note} if (ev.value & 0x0F) else set())
            elif ev.port == 0 and ev.reg in (0x00, 0x02, 0x04):
                periods = getattr(self, "_ssg_period", {})
                idx = ev.reg // 2
                periods[(inst, idx)] = (periods.get((inst, idx), 0x100) & 0xF00) | ev.value
                self._ssg_period = periods
            elif ev.port == 0 and ev.reg in (0x01, 0x03, 0x05):
                periods = getattr(self, "_ssg_period", {})
                idx = ev.reg // 2
                periods[(inst, idx)] = (periods.get((inst, idx), 0x100) & 0x0FF) | ((ev.value & 0x0F) << 8)
                self._ssg_period = periods
            elif ev.port == 0 and ev.reg == 0x10:
                for i in range(6):
                    if ev.value & (1 << i): self.rhythm.trigger(i)
            elif ev.port == 1 and ev.reg == 0x00:
                key = self._resolve_key("YM2608", "ADPCM", 0, inst)
                if key is None: return
                if ev.value & 0x80: self._set_row_notes(key, {60})
                elif ev.value & 0x01: self._set_row_notes(key, {60})
                else: self._set_row_notes(key, set())
        elif ev.chip == "YM2151" and ev.reg == 0x08:
            ch = ev.value & 0x07
            key = self._resolve_key("YM2151", "FM", ch, inst)
            if key is None: return
            if ev.value & 0x78:
                note = self._fm_note_2151(inst, ch)
                self._set_row_notes(key, {note} if note is not None else set())
            else:
                self._set_row_notes(key, set())

    def _fm_note_2608(self, instance, channel):
        fnums = getattr(self, "_fnum2608", {})
        if (instance, channel) not in fnums: return 60
        fnum, block = fnums[(instance, channel)]
        freq = 7_987_200 * fnum * (2 ** block) / (144 * 1_048_576)
        return max(0, min(127, round(69 + 12 * math.log2(max(1, freq) / 440))) )

    def _fm_note_2151(self, instance, channel):
        fnums = getattr(self, "_fnum2151", {})
        if (instance, channel) not in fnums: return 60
        semitone, octave = fnums[(instance, channel)]
        return max(0, min(127, 36 + octave * 12 + semitone))
