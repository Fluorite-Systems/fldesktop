from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

import xkbcommon.xkb as xkb
import logging


class InputEventFilter(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._xkb_ctx = xkb.Context()
        self._xkb_keymap = None
        self._xkb_state = None

        self.set_layout("us")

    def set_layout(self, lang: str) -> None:
        "Set keyboard layout by language code"

        try:
            new_keymap = self._xkb_ctx.keymap_new_from_names(
                rules="evdev", model="pc105", layout=str(lang)
            )
            if new_keymap:
                self._xkb_keymap = new_keymap
                self._xkb_state = self._xkb_keymap.state_new()
        except Exception as e:
            logging.warning(f"Failed to set layout {lang}: {e}")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier |
                                    Qt.KeyboardModifier.AltModifier |
                                    Qt.KeyboardModifier.MetaModifier):
                return super().eventFilter(obj, event)

            scan_code = event.nativeScanCode()

            if scan_code and self._xkb_state and self._xkb_keymap:

                # scan_code += 8

                is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                is_caps = event.text().isupper() and not is_shift

                mods_depressed = 0
                if is_shift:
                    shift_idx = self._xkb_keymap.mod_get_index("Shift")
                    if shift_idx is not None and shift_idx >= 0:
                        mods_depressed |= (1 << shift_idx)

                mods_locked = 0
                if is_caps:
                    caps_idx = self._xkb_keymap.mod_get_index("Lock")
                    if caps_idx is not None and caps_idx >= 0:
                        mods_locked |= (1 << caps_idx)

                self._xkb_state.update_mask(
                    depressed_mods=mods_depressed, latched_mods=0, locked_mods=mods_locked,
                    depressed_layout=0, latched_layout=0, locked_layout=0
                )

                keysym = self._xkb_state.key_get_one_sym(scan_code)
                new_text = xkb.keysym_to_string(keysym)

                if new_text and new_text != event.text():
                    new_event = QKeyEvent(
                        event.type(),
                        event.key(),
                        event.modifiers(),
                        new_text,
                        event.isAutoRepeat(),
                        event.count()
                    )
                    QApplication.sendEvent(obj, new_event)
                    return True

        return super().eventFilter(obj, event)
