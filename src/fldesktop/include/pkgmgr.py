from PySide6.QtGui import QIcon
from PySide6.QtCore import QProcess
from pathlib import Path
import subprocess
import logging
import uuid
import json
import os


class Package:
    def __init__(self, path: str):
        self.package = ""
        self.name = ""
        self.generic_name = {}
        self.version = ""
        self.icon = QIcon()
        self.search = False
        self.executable = False
        self.path = path

        self.procs = []

        self.mount_path = Path(
            os.environ["XDG_RUNTIME_DIR"]
        ) / "fla" / str(uuid.uuid4())
        
        self.mount()
        self.load_metadata()

    def load_metadata(self):
        "Load package metadata"

        path = self.mount_path / "app.json"

        with open(path) as f:
            data = json.load(f)
        
        if "package" in data:
            self.package = data["package"]

        if "name" in data:
            self.name = data["name"]
        
        if "generic_name" in data:
            self.generic_name = data["generic_name"]

        d = os.listdir(self.mount_path)
        if "search" in d:
            self.search = True
        if "main" in d:
            self.executable = True
        if "icon.fvgi" in d:
            with open(self.mount_path / "icon.fvgi") as f:
                self.icon = f.read()

    def mount(self):
        "Mount app squashfs"

        logging.info(f"Mounting package from {self.path} to {self.mount_path}")

        os.makedirs(self.mount_path)
        subprocess.run(["squashfuse", self.path, self.mount_path])
    
    def unmount(self):

        logging.info(f"Unmounting package from {self.mount_path}")

        subprocess.run(["fusermount", "-u", self.mount_path])
        os.rmdir(self.mount_path)
    
    def exec(self, arguments: list = []):

        logging.debug(f"Executing entrypoint {self.mount_path / "main"}")

        if self.executable:

            proc = QProcess()
            proc.start(str(self.mount_path / "main"), arguments)

            self.procs.append(proc)

            # temporary solution, make it use bwrap instead


class PackageManager:
    def __init__(self, comm):
        self.comm = comm
        self.comm.register("pkgmgr", {
            "get_apps": self.get_apps,
            "run_app": self.run_app,
            "unmount": self.unmount
        })

        self.apps_path = self.comm.request(
            "osmgr", "get_path", "Applications"
        )
        self.packages = []
        self.loaded_packages = {}
        self.refresh_apps()

        self.load_apps()
    
    def refresh_apps(self):
        "Refreshes installed apps"

        logging.info("Refreshing package list...")

        try:
            for i in os.listdir(self.apps_path):
                if i.split(".")[-1] == "fla":
                    path = self.apps_path + "/" + i
                    self.packages.append(path)
        except Exception as e:
            print(e)
        
    def load_apps(self):
        "Load and mount packages"

        for i in self.packages:
            package = Package(i)
            self.loaded_packages[package.package] = package

            logging.info(f"Loaded package {package.package}")
    
    def get_apps(self):
        "Return app list"

        return self.loaded_packages

    def run_app(self, package: str, arguments: list = []):
        "Run app by it's package name"

        if package in self.loaded_packages:
            self.loaded_packages[package].exec(arguments)
    
    def unmount(self):
        "Unmount packages"

        for i in self.loaded_packages:
            self.loaded_packages[i].unmount()
    
    def killall(self):
        "Kill all processes"

        for i in self.loaded_packages.values():
            for proc in i.procs:
                proc.kill()
