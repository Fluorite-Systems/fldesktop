from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject

from fldesktop.include.uikit.builder import Builder
from fldesktop.include.uikit.dnd import DragFilter, DropFilter
from fldesktop.include.uikit.widgets.base import Widget

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


class ClientManager(QObject):
    process_event_s = Signal(dict, str, Any)
    del_cl_objects_s = Signal(str)

    def __init__(self, comm):
        super().__init__()
        self.process_event_s.connect(self.process_event)
        self.del_cl_objects_s.connect(self.del_client_objects)

        self.comm = comm
        self.comm.register("clientmgr", {
            "process_event": lambda *a: self.process_event_s.emit(*a),
            "del_client_objects": lambda *a: self.del_cl_objects_s.emit(*a)
        })

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

    def del_client_objects(self, handler_uuid: str):

        objects = self.comm.request(
            "fs3", "query", {"Attrs.UI.ClientHandlerUUID": handler_uuid}
        )
        for obj in objects:
            self.comm.request("fs3", "delete_node", obj)