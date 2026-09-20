from fldesktop.include.compositor.widgets import widgets
from fldesktop.include.compositor.widgets.base import Widget

import logging
import locale


class Builder:
    def __init__(self, cm):

        self.cm = cm

        self.clients = {}
        self.widgets = {}
        self.translations = {}

    def create_widget(self, node_id: int, node_attrs: dict):

        logging.debug(
            f"Creating widget from node {node_id} with attrs {node_attrs}"
        )

        wtype = node_attrs["Attr.System.Type"].split(".")[-1].lower()

        wname = node_id#f"{wtype}_{node_id}"

        widget = widgets[wtype](self, wname, node_attrs)

        self.widgets[wname] = widget

    def process_relation(self, node_id: int, node_attrs: dict):

        logging.debug(
            f"Processing relation with id {node_id}, attrs {node_attrs}"
        )

        logging.debug(f"{self.clients}, {self.widgets}")

        if "Attr.Relation.From" in node_attrs:
            rfrom = node_attrs["Attr.Relation.From"]
            if rfrom not in self.widgets and rfrom not in self.clients:
                return
        else:
            return

        if "Attr.Relation.To" in node_attrs:
            rto = node_attrs["Attr.Relation.To"]
            if rto not in self.widgets:
                return
        else:
            return

        logging.debug("passed")

        if rfrom in self.widgets:
            self.widgets[rto].reparent(self.widgets[rfrom])
        elif rfrom in self.clients:
            self.widgets[rto].reparent(self.clients[rfrom])

    def event(self, node, **kwargs):

        if "Attrs.UI.ClientHandlerUUID" not in node.props:
            return

        self.cm.process_widget_callback(
            node.props["Attrs.UI.ClientHandlerUUID"],
            kwargs
        )