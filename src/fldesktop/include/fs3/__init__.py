from fldesktop.include.fs3 import db, resolver


class FS3:
    def __init__(self, comm):

        self.comm = comm

        self.db = db.DatabaseManager(self)
        self.resolver = resolver.Resolver(self, self.db)

        self.comm.register(
            "fs3", {
                "create_node": self.resolver.create_node,
                "delete_node": self.resolver.delete_node,
                "set_attrs": self.resolver.set_attrs,
                "del_attrs": self.resolver.del_attrs,
                "get_attr": self.resolver.get_attr,
                "get_attrs": self.resolver.get_attrs,
                "query": self.resolver.query,
                "open": self.resolver.open
            }
        )

    def emit_event(self, type: str = "modified", **kwargs):

        self.comm.emit(
            f"fs3_node_{type}", **kwargs
        )

    def srv_cleanup(self):

        self.db.stop_thread()