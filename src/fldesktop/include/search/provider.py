import subprocess
import json
import os


class SearchProvider:
    def __init__(self, bin_path: str, name: str):

        self.binary = bin_path
        self.name = name
    
    def query(self, query: str):
        "Do a search query"

        try:

            result = subprocess.run(
                [self.binary, query],
                cwd=os.path.dirname(self.binary),
                capture_output=True, text=True
            )
            result = json.loads(result.stdout)

            return result
        except:
            return []