class GarbageCollector:
    def __init__(self, db):

        self.db = db

    def is_save_needed(self, tr):
        "Prevent saving unneccesary nodes"

        if "wal_load" in tr:
            return False
        
        if tr["method"] == "create_node":
            if "Attr.System.Type" in tr["attrs"]:
                if str(tr["attrs"]["Attr.System.Type"]).startswith("Node.UI"):
                    return False
                
                if str(tr["attrs"]["Attr.System.Type"]) == "Node.Relation":
                    if "Attr.Relation.From" in tr["attrs"] \
                        and "Attr.Relation.To" in tr["attrs"]:
                        rfrom = tr["attrs"]["Attr.Relation.From"]
                        rto = tr["attrs"]["Attr.Relation.To"]
                        if rfrom in self.db.db:
                            if self.db.db[rfrom].attrs["Attr.System.Type"] \
                                .startswith("Node.UI"):
                                return False
                        if rto in self.db.db:
                            if self.db.db[rto].attrs["Attr.System.Type"] \
                                .startswith("Node.UI"):
                                return False

        return True

    def run(self):
        "Run garbace collection"

        # here comes nothing...