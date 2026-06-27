class AppSearch:
    def __init__(self, comm):
        self.comm = comm
        self.name = self.comm.request("localemgr", "tr", "Applications")
    
    def query(self, query: str):

        query = query.lower()
        results = []
        apps = self.comm.request("pkgmgr", "get_apps")

        for app in apps.values():
            if query in app.package.lower() or \
                query in app.name.lower():
                if app.executable:
                    i = {
                        "title": app.name,
                        "description": app.package,
                        #"icon": None,
                        "callback": app.exec
                    }
                    results.append(i)
        
        result = [{
            "type": "items",
            "items": results
        }]

        return result
