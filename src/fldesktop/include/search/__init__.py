from PySide6.QtGui import QIcon
from fldesktop.include.search.ui import SearchBtn
from fldesktop.include.search.provider import SearchProvider
from fldesktop.include.search.appsearch import AppSearch

import logging


class Search:
    def __init__(self, comm):
        self.comm = comm

        self.comm.register("search", {
            "get_btn": self.get_btn,
            "search": self.search
        })

        self.providers = []
        self.load_providers()
    
    def get_btn(self) -> SearchBtn:
        "Create and return search button"
        self.btn = SearchBtn(self.comm)

        return self.btn

    def load_providers(self):
        "Load search providers"

        apps = self.comm.request("pkgmgr", "get_apps")

        for app in apps.values():
            if app.search:
                provider = SearchProvider(f"{app.mount_path}search", app.name)
                logging.info(f"Loaded search provider {app.name}")
                self.providers.append(provider)

        self.providers.append(AppSearch(self.comm))
    
    def rectify(self, results: dict) -> dict:
        
        for pr in results.keys():
            p = results[pr]

            if type(p) != list:
                p = [p]
            for v in p:
                if not "type" in v:
                    p.remove(v)
                    continue
                
                if v["type"] == "review":
                    if not "text" in v:
                        v["text"] = ""
                    if not "images" in v:
                        v["images"] = []

                    if not v["text"] and not v["images"]:
                        p.remove(v)
                        continue

                elif v["type"] == "items":
                    print(v)
                    if not "items" in v:
                        p.remove(v)
                        continue
                    
                    if not len(v["items"]):
                        p.remove(v)
                        continue

                    for i in v["items"]:
                        if not "title" in i:
                            i["title"] = ""
                        if not "description" in i:
                            i["description"] = ""
                        if not "icon" in i:
                            i["icon"] = QIcon().fromTheme("question-symbolic")
                        else:
                            ...

                # to be continued
        
        rresults = {k: v for k, v in results.items() if v}
        
        return rresults
    
    def search(self, query: str) -> dict:
        "Perform a search"
        results = {}

        for i in self.providers:
            r = i.query(query)
            results[i.name] = r

        return self.rectify(results)