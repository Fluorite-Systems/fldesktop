from fldesktop.include.uikit import builder


class UIKit:
    def __init__(self, comm):

        self.comm = comm

        self.comm.subscribe("fs3_node_created", self.on_fs3_node_created)
        self.comm.subscribe("fs3_node_modified", self.on_fs3_node_modified)
        self.comm.subscribe("fs3_node_deleted", self.on_fs3_node_deleted)

        self.builder = builder.Builder(self)

    def on_fs3_node_created(self, id: int, attrs: dict):

        if "Attr.System.Type" in attrs:
            if isinstance(attrs["Attr.System.Type"], str):

                if attrs["Attr.System.Type"] == "Node.UI.Window":

                    self.builder.create_window(id, attrs)

                elif attrs["Attr.System.Type"].startswith("Node.UI.Applet"):

                    self.builder.create_applet(id, attrs)

                elif attrs["Attr.System.Type"].startswith("Node.UI.Widget"):

                    self.builder.create_widget(id, attrs)

                elif attrs["Attr.System.Type"] == "Node.Relation":

                    self.builder.process_relation(id, attrs)

    def on_fs3_node_modified(self, id: str, attrs: dict):

        self.builder.on_node_modified(id)

    def on_fs3_node_deleted(self, id: str):

        self.builder.on_node_deleted(id)

    def process_widget_callback(self, handler_uuid: str, data):

        self.comm.request(
            "appserver", "handler_callback", handler_uuid, data
        )
