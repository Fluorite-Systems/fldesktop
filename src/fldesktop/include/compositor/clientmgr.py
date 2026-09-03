from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject

from fldesktop.include.compositor.parser import Parser

from typing import Any

import json
import msgpack
import logging


class Client:
    def __init__(self, comm, name: str, pkg: str, 
                 wsize: tuple, wtype: str,
                 uuid: str, callback: Signal):
        self.comm = comm
        self.name = name
        self.package = pkg
        self.callback = callback
        self.widget = QWidget()
        self.main_layout = QVBoxLayout(self.widget)
        self.widgets = {}
        self.deleted_widgets = []
        self.translations = {}
        self.parser = Parser(self)
        self.uuid = uuid
    
        # Create a window
        self.winid, self.on_close = self.comm.request(
            "wm", "create_window", self.name, self.widget,
            QIcon(), self.package, wsize, wtype
        )

        self.on_close.connect(lambda: self.callback("close"))
    
    def event_bk(self, wname: str, type: str, data: dict) -> None:
        e = {
            "name": wname,
            "type": type,
            "data": data
        }

        self.callback(json.dumps(e))
    
    def event(self, **kwargs) -> None:

        self.callback(json.dumps(kwargs))

    def receive(self, data: dict):
        "Receive some info from backend"

        #logging.debug(f"Got data from client {self.uuid}: {data}")

        match data["type"]:
            case "init_layout":
                self.deleted_widgets = []

                for k in list(self.widgets.keys()):
                    if k in self.widgets:
                        w = self.widgets[k]
                        w.delete()

                self.parser.build(data["payload"])
                self.widget.update()

                self.callback(
                    json.dumps(
                        {
                            "status": "ok",
                            "deleted": self.deleted_widgets
                        }
                    )
                )
                self.deleted_widgets = []

            case "set_translations":
                self.translations = data["translations"]
                self.callback('{"status": "ok"}')

            case "update_children":
                if data["name"] in self.widgets:
                    self.deleted_widgets = []
                    self.widgets[data["name"]].update_children(data["children"])
                    for w in self.widgets:
                        logging.debug(f"Widget {w} has {self.widgets[w].children}")
                    self.callback(
                        json.dumps(
                            {
                                "status": "ok",
                                "deleted": self.deleted_widgets
                            }
                        )
                    )
                    self.deleted_widgets = []
                else:
                    self.callback('{"status": "unknown_widget"}')

            case "add_children":
                if data["name"] in self.widgets:
                    self.widgets[data["name"]].add_children(data["children"])
                    self.callback('{"status": "ok"}')
                else:
                    self.callback('{"status": "unknown_widget"}')

            case "delete_children":
                if data["name"] in self.widgets: 
                    self.deleted_widgets = []
                    self.widgets[data["name"]].delete_children(data["children"]) 
                    self.callback(
                        json.dumps(
                            {
                                "status": "ok",
                                "deleted": self.deleted_widgets
                            }
                        )
                    )
                    self.deleted_widgets = []
                else:
                    self.callback('{"status": "unknown_widget"}')


            case "clear_children":
                if data["name"] in self.widgets:
                    self.deleted_widgets = []
                    self.widgets[data["name"]].clear_children()
                    self.callback(
                        json.dumps(
                            {
                                "status": "ok",
                                "deleted": self.deleted_widgets
                            }
                        )
                    )
                    self.deleted_widgets = []
                else:
                    self.callback('{"status": "unknown_widget"}')

            case "call_method":
                if data["name"] in self.widgets:
                    w = self.widgets[data["name"]]
                    if data["method"] in w.callables:
                        r = w.callables[data["method"]](**data["args"])

                        if r or str(data["method"]).startswith("get"):
                            self.callback(
                                json.dumps({"status": "ok", "reply": r})
                            )
                        else:
                            self.callback('{"status": "ok"}')
                else:
                    self.callback('{"status": "unknown_widget"}')

            case "append_title":
                if "title" in data:
                    self.comm.request("wm", "append_window_title",
                                self.winid, data["title"])
                    self.callback('{"status": "ok"}')

            case "spawn_effect":
                if "effect" in data:
                    self.comm.request(
                        "wm", "spawn_effect", self.winid, data["effect"]
                    )
                    self.callback('{"status": "ok"}')

            case "file_dialog":
                dtype = "open_file"
                if "dialog_type" in data:
                    if data["dialog_type"] == "save_file":
                        dtype = "save_file"
                self.comm.request(
                    "dialogmgr", dtype,
                    lambda r: self.callback(
                        json.dumps({"type": "files_choosen", "files": r})
                    )
                )
                self.callback('{"status": "ok"}')
            case _:
                self.callback('{"status": "invalid_type"}')

    def cleanup(self):
        "Clean up on close"

        while self.widgets:
            key = next(iter(self.widgets))
            self.widgets[key].delete()


class ClientManager(QObject):
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
