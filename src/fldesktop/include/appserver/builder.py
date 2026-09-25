from fldesktop.include.appserver.widgets import widgets
from fldesktop.include.appserver.widgets.base import Widget
from fldesktop.include.appletmgr.applet import Applet

import logging
import locale


class Builder:
    def __init__(self, cm):

        self.cm = cm

        self.objects = {}
        self.translations = {}

    def create_applet(self, node_id: str, node_attrs: dict):

        self.objects[node_id] = Applet(self.cm.comm)

    def create_widget(self, node_id: int, node_attrs: dict):

        logging.debug(
            f"Creating widget from node {node_id} with attrs {node_attrs}"
        )

        wtype = node_attrs["Attr.System.Type"].split(".")[-1].lower()

        wname = node_id#f"{wtype}_{node_id}"

        widget = widgets[wtype](self, wname, node_attrs)

        self.objects[wname] = widget

    def process_relation(self, node_id: int, node_attrs: dict):

        logging.debug(
            f"Processing relation with id {node_id}, attrs {node_attrs}"
        )

        logging.debug(f"{self.objects}, {self.objects}")

        if "Attr.Relation.From" in node_attrs:
            rfrom = node_attrs["Attr.Relation.From"]
            if rfrom not in self.objects:
                return
        else:
            return

        if "Attr.Relation.To" in node_attrs:
            rto = node_attrs["Attr.Relation.To"]
            if rto not in self.objects:
                return
        else:
            return

        logging.debug("passed")

        if rfrom in self.objects:
            self.objects[rto].reparent(self.objects[rfrom])

    def call_method(self, id, method, kwargs):

        if id in self.objects:
            if method in self.objects[id].callables:
                return self.objects[id].callables[method](**kwargs)

        if id in self.objects:
            if method in self.objects[id].callables:
                return self.objects[id].callables[method](**kwargs)

    def event(self, node, **kwargs):

        if "Attrs.UI.ClientHandlerUUID" not in node.props:
            return

        self.cm.process_widget_callback(
            node.props["Attrs.UI.ClientHandlerUUID"],
            kwargs
        )