class UI:
    def __init__(self, comm, name, attrs: dict = {}, baseattrs: dict = {}):

        self.comm = comm

        self.name = name
        self.attrs = attrs
        self.baseattrs = baseattrs
        self.callables = {}

        self.apply_attrs()

    def apply_attrs(self):

        for attr in self.baseattrs:
            if attr not in self.attrs:
                self.attrs[attr] = self.baseattrs[attr]
            if type(self.attrs[attr]) != type(self.baseattrs[attr]):
                self.attrs[attr] = self.baseattrs[attr]

    def event(self, **kwargs):

        if "Attrs.UI.ClientHandlerUUID" not in self.attrs:
            return

        kwargs["name"] = self.name

        self.comm.request(
            "appserver", "handler_callback",
            self.attrs["Attrs.UI.ClientHandlerUUID"],
            kwargs
        )