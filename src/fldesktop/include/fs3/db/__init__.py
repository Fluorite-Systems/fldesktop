from PySide6.QtCore import QObject, Signal, QTimer
from fldesktop.include.fs3.models import Node
from fldesktop.include.fs3.db.storagemgr import StorageManager
from fldesktop.include.fs3.db.gc import GarbageCollector
import threading
import uuid
import base64
import logging
import time
import queue


class Database:
    def __init__(self, callback, storage_path):

        self.callback = callback
        self.db = {}
        self.index = {}

        self.queue = queue.Queue()
        self.replies = {}
        self.lock = threading.Lock()
        self.stop = threading.Event()

        self.gc = GarbageCollector(self)
        self.storage = StorageManager(self, storage_path)
        self.storage.load()

    def create_node(self, attrs: dict = {}) -> None:

        uuid4 = base64.urlsafe_b64encode(uuid.uuid4().bytes) \
            .decode().rstrip("=")

        logging.debug(f"Creating node with attrs {attrs} and id {uuid4}")

        node = Node(uuid4, attrs)

        self.db[uuid4] = node

        self.update_index(uuid4)

        self.callback.emit("created", {"id": uuid4, "attrs": attrs})

        return uuid4

    def delete_node(self, id: int) -> None:

        logging.debug(f"Deleting node with id {id}")

        if id in self.db:
            self.db.pop(id)

        self.callback.emit("deleted", {"id": int})

        self.gc.run()

    def set_attrs(self, id: int, attrs: dict) -> None:

        if id in self.db:
            self.db[id].attrs.update(attrs)

        self.update_index(id)

        self.callback.emit("modified", {"id": int, "attrs": attrs})

    def get_node(self, id: int) -> dict | None:

        with self.lock:
            if id in self.db:
                return self.db[id].attrs

    def get_nodes(self) -> dict[int, Node]:

        with self.lock:
            return self.db

    def query_by_attr_value(self, attr: str, value) -> list | None:

        with self.lock:
            if (attr, value) in self.index:
                return self.index[(attr, value)]

    def update_index(self, id: int) -> None:

        if not id in self.db:
            return

        for attr, val in self.db[id].attrs.items():
            name = (attr, val)
            if name in self.index:
                self.index[name].append(id)
            else:
                self.index[name] = [id]

    def sched_transaction(self, **kwargs):

        self.queue.put(kwargs)

    def run_transaction(self, **kwargs):

        logging.debug(f"Running transaction {kwargs}")

        with self.lock:
            try:
                if "method" not in kwargs or "tr_id" not in kwargs:
                    return

                match kwargs["method"]:
                    case "create_node":
                        if "attrs" not in kwargs:
                            return
                        self.replies[kwargs["tr_id"]] = \
                            self.create_node(kwargs["attrs"])

                    case "delete_node":
                        if "id" not in kwargs:
                            return
                        self.replies[kwargs["tr_id"]] = \
                            self.delete_node(kwargs["id"])

                    case _:
                        return

                if self.gc.is_save_needed(kwargs):
                    self.storage.append(kwargs)
            except Exception as e:
                logging.critical(f"Failed to run transaction: {str(e)}")

    def mainloop(self):

        while not self.stop.is_set():
            ts = self.queue.get()
            self.run_transaction(**ts)


class DatabaseManager(QObject):

    thread_callback = Signal(str, dict)

    def __init__(self, core):
        super().__init__()

        self.core = core

        self.thread_callback.connect(
            lambda s, kwargs: self.core.emit_event(s, **kwargs)
        )

        storage_path = self.core.comm.request("osmgr", "get_path", "fs3")
        if not storage_path:
            storage_path = "/system/fs3"

        self.db = Database(self.thread_callback, storage_path)
        self.db_thread = threading.Thread(
            target=self.db.mainloop,
            daemon=False
        )
        self.db_thread.start()

    def create_node(self, attrs: dict):

        tr_id = str(uuid.uuid4())

        self.db.sched_transaction(
            method="create_node", attrs=attrs,
            tr_id=tr_id
        )

        while tr_id not in self.db.replies:
            time.sleep(0.001)

        return self.db.replies.pop(tr_id)

    def delete_node(self, id: int):

        tr_id = str(uuid.uuid4())

        self.db.sched_transaction(
            method="delete_node", id=id,
            tr_id=tr_id
        )

        while tr_id not in self.db.replies:
            time.sleep(0.001)

        return self.db.replies.pop(tr_id)

    def set_attrs(self, id: int, attrs: dict):

        tr_id = str(uuid.uuid4())

        self.db.sched_transaction(
            method="set_attrs", 
            id=id, attrs=attrs, tr_id=tr_id
        )

        while tr_id not in self.db.replies:
            time.sleep(0.001)

        return self.db.replies.pop(tr_id)

    def get_node(self, id: int):

        return self.db.get_node(id)

    def get_nodes(self):

        return self.db.get_nodes()

    def query_by_attr_value(self, attr: str, value):

        return self.db.query_by_attr_value(attr, value)

    def stop_thread(self):

        self.db.stop.set()
        self.db.sched_transaction(method="shutdown")
        self.db_thread.join()