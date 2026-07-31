from typing import Any

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject
from fldesktop.include.compositor.parser import Parser

import json
import logging


class Client:
    def __init__(self, comm, name: str, uuid: str, pkg: str, callback: Signal):
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
            "wm", "create_window",
            {
                "name": self.name,
                "package": self.package,
                "icon": QIcon(),
                "widget": self.widget
            }
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
                    self.callback('{"status": "unknown_node"}')

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
                    self.callback('{"status": "unknown_node"}')

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
                    self.comm.send("wm", "append_window_title",
                                self.winid, data["title"])
                    self.callback('{"status": "ok"}')

            case "file_dialog":
                dtype = "open_file"
                if "dialog_type" in data:
                    if data["dialog_type"] == "save_file":
                        dtype = "save_file"
                self.comm.send(
                    "dialogmgr", dtype,
                    lambda r: self.callback(
                        json.dumps({"type": "files_choosen", "files": r})
                    )
                )
                self.callback('{"status": "ok"}')
            case _:
                self.callback('{"status": "invalid_type"}')


class ClientManager(QObject):
    new_client_s = Signal(str, str, str, Any)
    notify_client_s = Signal(str, str)
    kill_client_s = Signal(str)

    def __init__(self, comm):
        super().__init__()
        self.new_client_s.connect(self.new_client)
        self.notify_client_s.connect(self.notify_client)
        self.kill_client_s.connect(self.kill_client)


        self.comm = comm
        self.comm.register("clientmgr", {
            "new_client": lambda n, u, p, c:
                self.new_client_s.emit(n, u, p, c),
            "notify_client": lambda u, d:
                self.notify_client_s.emit(u, json.dumps(d)),
            "kill_client": lambda u: 
                self.kill_client_s.emit(u)
        })

        self.clients = {}

    def new_client(self, name: str, uuid: str, package: str,
                   callback: Any):
        "Create a new client"

        cl = Client(self.comm, name, package, uuid, callback)
        self.clients[cl.uuid] = cl
    
    def notify_client(self, uuid: str, data: str):
        "Notify client"

        data = json.loads(data)

        if uuid in self.clients:
            self.clients[uuid].receive(data)
        else:
            print(uuid, "is not in clients", type(uuid))
        
    def kill_client(self, uuid: str):
        "Kill client"

        logging.debug(f"Trying to kill client {uuid}")
        if uuid in self.clients:
            self.comm.send("wm", "close_window", self.clients[uuid].winid)
