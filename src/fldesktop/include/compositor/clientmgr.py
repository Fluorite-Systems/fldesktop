from inspect import ArgInfo
from operator import call

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject

from fldesktop.include.compositor.builder import Builder
from fldesktop.include.compositor.dnd import DragFilter, DropFilter
from fldesktop.include.compositor.widgets.base import Widget

from typing import Any

import msgpack
import logging


REQ_TYPES = {
    "create_node": {
        "attrs": dict
    },
    "delete_node": {
        "id": str
    },
    "set_attrs": {
        "id": str,
        "attrs": dict
    },
    "del_attrs": {
        "id": str,
        "attrs": list
    },
    "get_attr": {
        "id": str,
        "attr": str
    },
    "get_attrs": {
        "id": str
    },
    "query": {
        "attrs": dict
    },
    "open": {
        "id": str,
        "mode": str
    },
    "call_method": {
        "id": str,
        "method": str,
        "args": dict
    }
}


class Client:
    def __init__(self, comm, uuid: str, callback: Signal,
                 title: str, package: str, 
                 width: int, height: int, type: str):
        self.comm = comm
        self.title = title
        self.package = package
        self.callback = callback
        self.widget = QWidget()
        self.qlayout = QVBoxLayout(self.widget)
        self.widgets = {}
        self.deleted_widgets = []
        self.translations = {}
        self.callables = {}
        self.uuid = uuid
        self.drag_filter = DragFilter(self.widget)
        self.drop_filter = DropFilter(self.widget)
    
        # Create a window
        self.winid, self.on_close = self.comm.request(
            "wm", "create_window", self.title, self.widget,
            self.get_win_icon(), self.package, (width, height), type
        )

        self.on_close.connect(lambda: self.callback("close"))
    
    def event(self, **kwargs) -> None:

        self.callback(kwargs)

    def cleanup(self):
        "Clean up on close"

        while self.widgets:
            key = next(iter(self.widgets))
            self.widgets[key].delete()

    def get_win_icon(self):

        pkgs = self.comm.request("pkgmgr", "get_apps")

        for name, value in pkgs.items():
            if name == self.package:
                return value.icon

        return QIcon()


class ClientManagerOld(QObject):
    new_client_s = Signal(str, str, str, tuple, str, Any)
    notify_client_s = Signal(str, bytes)
    kill_client_s = Signal(str)

    def __init__(self, comm):
        super().__init__()
        self.new_client_s.connect(self.new_client)
        self.notify_client_s.connect(self.notify_client)
        self.kill_client_s.connect(self.kill_client)


        self.comm = comm
        self.comm.register("clientmgr", {
            "new_client": lambda u, n, p, s, t, c:
                self.new_client_s.emit(u, n, p, s, t, c),
            "notify_client": lambda u, d:
                self.notify_client_s.emit(u, msgpack.packb(d)),
            "kill_client": lambda u: 
                self.kill_client_s.emit(u)
        })

        self.clients = {}

    def new_client(self, uuid: str, name: str, package: str,
                   wsize: tuple, wtype: str, callback: Any):
        "Create a new client"

        cl = Client(
            self.comm, name, package, wsize, wtype, uuid, callback
        )
        self.clients[cl.uuid] = cl
    
    def notify_client(self, uuid: str, data: bytes):
        "Notify client"

        data = msgpack.unpackb(data, strict_map_key=False)

        if uuid in self.clients:
            self.clients[uuid].receive(data)
        else:
            print(uuid, "is not in clients", type(uuid))
        
    def kill_client(self, uuid: str):
        "Kill client"

        logging.debug(f"Trying to kill client {uuid}")
        if uuid in self.clients:
            self.clients[uuid].cleanup()
            self.comm.request("wm", "close_window", self.clients[uuid].winid)


class ClientManager(QObject):
    process_event_s = Signal(dict, str, Any)

    def __init__(self, comm):
        super().__init__()
        self.process_event_s.connect(self.process_event)

        self.comm = comm
        self.comm.register("clientmgr", {
            "process_event": lambda *a: self.process_event_s.emit(*a)
        })

        self.comm.subscribe("fs3_node_created", self.on_fs3_node_created)
        self.comm.subscribe("fs3_node_modified", self.on_fs3_node_modified)
        self.comm.subscribe("fs3_node_deleted", self.on_fs3_node_deleted)

        self.builder = Builder(self)

    def process_event(self, data: dict, handler_uuid: str, callback):

        logging.debug(f"Processing data {data}")

        if not self.check_integrity(data):
            callback({"status": "not ok"})

        reply = None

        if data["cmd"] in [
            "create_node", "delete_node",
            "set_attrs", "del_attrs",
            "get_attr", "get_attrs",
            "query", "open"
        ]:
            args_needed = REQ_TYPES[data["cmd"]]
            args = {k: v for k, v in data.items() if k in args_needed}
            if "attrs" in args:
                if "Attr.System.Type" in args["attrs"]:
                    if args["attrs"]["Attr.System.Type"] \
                        .startswith("Node.UI"):
                        args["attrs"]["Attrs.UI.ClientHandlerUUID"] \
                            = handler_uuid
                        
            reply = self.comm.request(
                "fs3", data["cmd"], **args
            )

        elif data["cmd"] == "call_method":
            reply = self.builder.call_method(
                data["id"], data["method"], data["args"]
            )

        if reply is not None:
            callback({"status": "ok", "reply": reply})
        else:
            callback({"status": "ok"})
        
    def check_integrity(self, event: dict):

        if not isinstance(event, dict):
            return False

        if "cmd" not in event:
            return False

        if not isinstance(event["cmd"], str):
            return False

        if event["cmd"] not in REQ_TYPES:
            return False

        for t in REQ_TYPES:
            if event["cmd"] == t:
                for key, value in REQ_TYPES[t].items():
                    if key not in event:
                        return False
                    if not isinstance(event[key], value):
                        return False

        return True

    def on_fs3_node_created(self, id: int, attrs: dict):

        if "Attr.System.Type" in attrs:
            if isinstance(attrs["Attr.System.Type"], str):
                if attrs["Attr.System.Type"] == "Node.UI.Window":

                    callback = print

                    params = {
                        "title": "App",
                        "package": "Unknown",
                        "width": 500,
                        "height": 300,
                        "type": "normal"
                    }
                    for i in ["Title", "Package", "Width", "Height", "Type"]:
                        param = f"Attr.UI.Window.{i}"
                        if param in attrs:
                            params[i.lower()] = attrs[param]

                    cl = Client(
                        self.comm, id, callback, **params
                    )
                    self.builder.clients[cl.uuid] = cl

                elif attrs["Attr.System.Type"].startswith("Node.UI.Widget"):

                    self.builder.create_widget(id, attrs)

                elif attrs["Attr.System.Type"] == "Node.Relation":

                    self.builder.process_relation(id, attrs)

    def on_fs3_node_modified(self, id: int, attrs: dict):

        ...

    def on_fs3_node_deleted(self, id: int):

        ...

    def process_widget_callback(self, handler_uuid: str, data):

        self.comm.request(
            "appserver", "handler_callback", handler_uuid, data
        )