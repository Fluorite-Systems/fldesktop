import json


class CacheManager:
    def __init__(self, comm):
        self.comm = comm
        
        self.comm.register("cache", {
            "get_pkg_icon": self.get_pkg_icon
        })

        self.cache_path = self.comm.request(
            "osmgr", "get_path", ".cache/fluorite/pkgcache/"
        )

        self.load_cache()
        self.sync_cache()
    
    def get_pkg_icon(self, package: str):

        return None

    def load_cache(self):

        file = self.cache_path + "cache.json"

        with open(file) as f:
            data = json.load(f)
        
        self.cache = data
    
    def sync_cache(self):
        "Sync cache"
    
    def fetch_apps_data(self):
        "Fetch applications data, such as icons"

        