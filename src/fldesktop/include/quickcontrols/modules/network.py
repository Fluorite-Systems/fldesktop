from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, QByteArray
from PySide6.QtDBus import (QDBusConnection, QDBusInterface, QDBusMessage,
                            QDBusArgument, QDBusObjectPath, QDBusVariant)

import os
import ctypes

try:
    libc = ctypes.CDLL(None)
except Exception:
    libc = ctypes.CDLL("libc.so.6")


NM_SERVICE = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"

NM_STATE_MAPPING = {
    0: "Unknown",
    10: "Asleep",
    20: "Disconnected from network",
    30: "Disconnecting...",
    40: "Connecting...",
    50: "Connected, local network only",
    60: "Connected to internal network",
    70: "Connected to the Internet"
}


class NetworkManagement:
    def __init__(self):
        self.bus = QDBusConnection.systemBus()

    def _extract_object_paths(self, dbus_arg) -> list:
        paths = []
        if isinstance(dbus_arg, QDBusArgument):
            try:
                null_fd = os.open(os.devnull, os.O_WRONLY)
                saved_stderr_fd = os.dup(2)

                libc.fflush(None)
                os.dup2(null_fd, 2)
                os.close(null_fd)

                dbus_arg.beginArray()
                while not dbus_arg.atEnd():
                    item = dbus_arg.asVariant()
                    if isinstance(item, QDBusObjectPath):
                        paths.append(item.path())
                    elif hasattr(item, "path"):
                        paths.append(item.path())
                    else:
                        paths.append(str(item))
                dbus_arg.endArray()
            except Exception:
                pass
            finally:
                libc.fflush(None)
                os.dup2(saved_stderr_fd, 2)
                os.close(saved_stderr_fd)

        elif isinstance(dbus_arg, list):
            for item in dbus_arg:
                paths.extend(self._extract_object_paths(item))
        return paths

    def _get_property(self, path: str, interface: str, property_name: str):
        if not path or path == "/":
            return None

        iface = QDBusInterface(
            NM_SERVICE, str(path), DBUS_PROPERTIES_IFACE, self.bus
        )
        if not iface.isValid():
            return None

        reply = iface.call("Get", interface, property_name)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            return None

        args = reply.arguments()
        if args and len(args) > 0:
            val = args[0]
            if hasattr(val, "value"):
                val = val.value()
            if isinstance(val, QDBusVariant) or hasattr(val, "variant"):
                val = val.variant()
            return val
        return None

    def _get_all_wifi_devices(self) -> list:
        nm_iface = QDBusInterface(NM_SERVICE, NM_PATH, NM_IFACE, self.bus)
        reply = nm_iface.call("GetDevices")
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            return []

        all_devices = self._extract_object_paths(reply.arguments())
        wifi_devices = []

        for dev_path in all_devices:
            dev_type = self._get_property(
                dev_path, "org.freedesktop.NetworkManager.Device", 
                "DeviceType"
            )
            if dev_type == 2:
                wifi_devices.append(dev_path)
        return wifi_devices

    def _count_available_access_points(self, wifi_devices: list) -> int:
        ap_set = set()
        for dev_path in wifi_devices:
            raw_aps = self._get_property(
                dev_path, "org.freedesktop.NetworkManager.Device.Wireless",
                "AccessPoints"
            )
            ap_paths = self._extract_object_paths(raw_aps)
            for ap in ap_paths:
                if ap and ap != "/":
                    ap_set.add(ap)
        return len(ap_set)

    def get_status(self) -> dict:
        result = {
            "connected": False,
            "type": "Unknown",
            "state_code": 0,
            "wifi_enabled": False,
            "available_ap_count": 0,
            "ssid": None,
            "rssi": None,
            "strength": None
        }

        if not self.bus.isConnected():
            return result

        raw_state = self._get_property(NM_PATH, NM_IFACE, "State")
        if raw_state is not None:
            try:
                result["state_code"] = int(raw_state)
            except (ValueError, TypeError):
                pass

        wifi_switched_on = self._get_property(
            NM_PATH, NM_IFACE, "WirelessEnabled"
        )
        wifi_hw_on = self._get_property(
            NM_PATH, NM_IFACE, "WirelessHardwareEnabled"
        )
        result["wifi_enabled"] = bool(wifi_switched_on) and bool(wifi_hw_on)

        wifi_devices = self._get_all_wifi_devices()
        if result["wifi_enabled"] and wifi_devices:
            result["available_ap_count"] = \
                self._count_available_access_points(wifi_devices)

        raw_active = self._get_property(
            NM_PATH, NM_IFACE, "ActiveConnections"
        )
        active_connections = self._extract_object_paths(raw_active)

        if not active_connections:
            return result

        for conn_path in active_connections:
            if not conn_path or conn_path == "/":
                continue

            conn_type = self._get_property(
                conn_path, "org.freedesktop.NetworkManager.Connection.Active",
                "Type"
            )
            if not conn_type or "loopback" in str(conn_type).lower():
                continue

            result["connected"] = True
            result["type"] = str(conn_type)

            if "wireless" in str(conn_type).lower():
                raw_devices = self._get_property(
                    conn_path,
                    "org.freedesktop.NetworkManager.Connection.Active",
                    "Devices"
                )
                devices = self._extract_object_paths(raw_devices)
                if not devices:
                    continue

                dev_path = devices[0] if isinstance(devices, list) and \
                    len(devices) > 0 else str(devices)
                raw_ap = self._get_property(
                    dev_path,
                    "org.freedesktop.NetworkManager.Device.Wireless",
                    "ActiveAccessPoint"
                )

                ap_path = None
                if isinstance(raw_ap, QDBusObjectPath):
                    ap_path = raw_ap.path()
                elif hasattr(raw_ap, "path"):
                    ap_path = raw_ap.path()
                elif raw_ap:
                    ap_path = str(raw_ap)

                if ap_path and ap_path != "/":
                    raw_ssid = self._get_property(
                        ap_path, "org.freedesktop.NetworkManager.AccessPoint",
                        "Ssid"
                    )
                    strength = self._get_property(
                        ap_path, "org.freedesktop.NetworkManager.AccessPoint",
                        "Strength"
                    )

                    if isinstance(raw_ssid, QByteArray):
                        ssid = raw_ssid.data().decode("utf-8", errors="ignore")
                    elif isinstance(raw_ssid, bytes):
                        ssid = raw_ssid.decode("utf-8", errors="ignore")
                    else:
                        ssid = str(raw_ssid) if raw_ssid else None

                    result["ssid"] = ssid

                    if strength is not None:
                        try:
                            strength_val = int(strength)
                            result["strength"] = strength_val
                            result["rssi"] = (strength_val // 2) - 100
                        except (ValueError, TypeError):
                            pass
            break

        return result


class Network(QWidget):
    def __init__(self, comm, parent):
        super().__init__()

        self.comm = comm

        self.nm = NetworkManagement()

        self.setFixedHeight(50)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.text_layout = QVBoxLayout()

        self.status_icon = QLabel()
        self.status = QLabel()
        self.details = QLabel()

        self.layout.addWidget(self.status_icon)
        self.layout.addLayout(self.text_layout)
        self.text_layout.addStretch()
        self.text_layout.addWidget(self.status)
        self.text_layout.addWidget(self.details)
        self.text_layout.addStretch()
        self.layout.addStretch()

        self.timer = QTimer(interval=2500)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

        self.refresh()

    def refresh(self):

        status = self.nm.get_status()

        if status["connected"]:
            self.details.show()
            if status["wifi_enabled"]:
                self.details.setText(
                    f"{status["ssid"]}, {status["strength"]}%"
                )
            else:
                self.details.setText(
                    self.comm.request("localemgr", "tr", "Wired network")
                )
        else:
            self.details.setText("")
            self.details.hide()

        self.status.setText(
            self.comm.request(
                "localemgr", "tr",
                self.get_status_str(status)
            )
        )

        icon = self.comm.request("iconmgr", "get", self.get_icon(status))

        self.status_icon.setPixmap(icon.pixmap(46, 46))

        self.comm.request("qc_indicator", "add_icon", icon, "network")

    def get_icon(self, status: dict):

        icon = ""

        if status["connected"]:
            if status["wifi_enabled"]:
                strength = status["strength"]

                if strength >= 85:
                    icon = "network-wireless-signal-5"
                elif strength >= 70:
                    icon = "network-wireless-signal-4"
                elif strength >= 50:
                    icon = "network-wireless-signal-3"
                elif strength >= 35:
                    icon = "network-wireless-signal-2"
                elif strength >= 20:
                    icon = "network-wireless-signal-1"
                else:
                    icon = "network-wireless-signal-0"
            else:
                icon = "network-wired"
        else:
            if status["wifi_enabled"]:
                if status["available_ap_count"]:
                    icon = "network-wireless-available"
                else:
                    icon = "network-wireless-unavailable"
            else:
                icon = "network-wired-unavailable"

        return icon

    def get_status_str(self, status: dict):

        string = ""

        if status["connected"]:
            if status["state_code"] == 70:
                string = "Connected to the Internet"
            elif status["state_code"] == 60:
                string = "Connected to internal network"
            else:
                string = "Local network only"
        else:
            if status["wifi_enabled"]:
                if status["available_ap_count"]:
                    string = "Connections available"
                else:
                    string = "Connections unavailable"
            else:
                string = "Disconnected from network"

        return string
