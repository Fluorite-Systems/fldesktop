from fldesktop.include import (communicator, desktop, dialogs, lifecycle,
                     thememgr, pkgmgr, lockscreen, os_manager,
                     configmgr, appserver, search, wm, loginmgr,
                     localemgr, notifications, iconmgr, QApp,
                     PostInit, UserServiceStarter, fs3, appletmgr,
                     panel, startupscreen, extsvinit)
from fldesktop.include.appserver.clientmgr import ClientManager
from fldesktop.include.widgets.surface import SurfaceManager
from fldesktop.include.input import InputManager

import logging
import os
import traceback


SERVICES = {
    "LifeCycle": {
        "object": lifecycle.LifeCycle,
        "importance": "critical",
        "depends": ["ExtSvInit"],
        "runlevel": 1
    },
    "OSManager": {
        "object": os_manager.OSManager,
        "importance": "critical",
        "depends": ["QApplication"],
        "runlevel": 1
    },
    "ExtSvInit": {
        "object": extsvinit.ExtSvInit,
        "importance": "critical",
        "runlevel": 1
    },
    "FS3": {
        "object": fs3.FS3,
        "importance": "critical",
        "runlevel": 1
    },
    "ConfigManager": {
        "object": configmgr.ConfigurationManager,
        "importance": "critical",
        "depends": ["QApplication", "OSManager"],
        "runlevel": 1,
    },
    "LocaleManager": {
        "object": localemgr.LocaleManager,
        "importance": "critical",
        "depends": ["ConfigManager"],
        "runlevel": 1
    },
    "PackageManager": {
        "object": pkgmgr.PackageManager,
        "depends": ["QApplication", "IconManager"]
    },
    "Search": {
        "object": search.Search,
        "depends": ["PackageManager", "IconManager"]
    },
    "LoginManager": {
        "object": loginmgr.LoginManager,
        "depends": ["ConfigManager"]
    },
    "InputManager": {
        "object": InputManager,
        "depends": ["QApplication", "LocaleManager"]
    },
    "SurfaceManager": {
        "object": SurfaceManager,
        "importance": "critical",
        "depends": ["QApplication"],
        "runlevel": 1
    },
    "Desktop": {
        "object": desktop.Desktop,
        "importance": "critical",
        "depends": [
            "QApplication", "ConfigManager",
            "IconManager", "PackageManager",
            "SurfaceManager", "InputManager"
        ],
        "runlevel": 1
    },
    "QApplication": {
        "object": QApp,
        "importance": "critical",
        "depends": ["PreInit"],
        "runlevel": 1
    },
    "IconManager": {
        "object": iconmgr.IconManager,
        "importance": "critical",
        "depends": ["QApplication", "ThemingManager"]
    },
    "ThemingManager": {
        "object": thememgr.ThemingManager,
        "importance": "critical",
        "depends": ["QApplication"],
        "runlevel": 1
    },
    "WindowManager": {
        "object": wm.WindowManager,
        "importance": "critical",
        "depends": ["Desktop"]
    },
    "AppServer": {
        "object": appserver.AppServer,
        "depends": ["WindowManager"]
    },
    "ClientManager": {
        "object": ClientManager,
        "depends": ["AppServer"]
    },
    "StartupScreen": {
        "object": startupscreen.StartupScreenManager,
        "depends": ["Desktop"],
        "runlevel": 1
    },
    "Lockscreen": {
        "object": lockscreen.LockScreen,
        "depends": ["LoginManager", "Desktop"]
    },
    "Panel": {
        "object": panel.Panel,
        "depends": ["Desktop", "AppletManager"]
    },
    "NotifyManager": {
        "object": notifications.NotificationManager,
        "depends": ["Desktop"]
    },
    "DialogManager": {
        "object": dialogs.DialogManager,
        "depends": ["WindowManager"]
    },
    "AppletManager": {
        "object": appletmgr.AppletManager,
        "depends": ["Desktop"]
    },
    "PostInit": {
        "object": PostInit,
        "depends": ["QApplication"],
        "runlevel": 2
    },
    "QtEventLoop": {
        "object": QApp.exec,
        "importance": "critical",
        "restart": True,
        "depends": ["QApplication"],
        "runlevel": 1
    }
}

DEFAULTS = [
    ("object", lambda: ...), ("importance", "optional"),
    ("runlevel", 2), ("depends", []), ("restart", False)
]


class Service:
    def __init__(self, name: str, params: dict, comm) -> None:

        self.name = name
        self.comm = comm

        self.started = False

        for i in DEFAULTS:
            if i[0] in params:
                setattr(self, i[0], params[i[0]])
            else:
                setattr(self, i[0], i[1])

    def start(self) -> None:
        "Start service and catch exceptions"

        if self.started:
            return

        logging.info(f"Starting service {self.name}")

        try:
            self.object = self.object(self.comm)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]

            file = tb.filename.split("/")[-1]

            logging.critical(
                f"Service {self.name} failed: {file}, line {tb.lineno}: {e}"
            )

            if self.restart:
                self.start()

            if self.importance == "critical":
                self.comm.request("init", "failure")
        else:
            self.started = True
            self.comm.emit(f"init_started_{self.name}")

    def cleanup(self) -> None:
        "Cleanup service (if supported by object)"

        if hasattr(self.object, "srv_cleanup") and self.started:
            logging.info(f"Performing cleanup for service {self.name}")

            try:
                self.object.srv_cleanup()
            except Exception as e:
                logging.info(f"Cleanup for {self.name} failed: {e}")


class Init:
    def __init__(self):
        
        self.comm = communicator.Communicator()

        self.comm.register(
            "init",
            {
                "run": self.run,
                "cleanup": self.cleanup,
                "failure": self.on_failure
            }
        )

        self.resolve_services()

    def resolve_services(self) -> None:
        "Resolve services dependencies and make service list"

        services = []

        for name, params in SERVICES.items():
            services.append(Service(name, params, self.comm))

        self.services = list(services)
        n = len(self.services)
        
        for _ in range(n):
            changed = False
            for i in range(n):
                dependencies = getattr(self.services[i], "depends", [])
                
                for dep in dependencies:
                    dep_index = next((
                        idx for idx, el in enumerate(self.services) \
                            if el.name == dep
                    ), -1)
                    
                    if dep_index > i:
                        self.services.insert(i, self.services.pop(dep_index))
                        changed = True
            
            if not changed:
                break

        logging.debug("Running these services:")
        for s in self.services:
            logging.debug(s.name)
                
    def run(self, runlevel: int = 1) -> None:
        "Start services"

        logging.info("Starting services...")
        
        for service in self.services:
            if service.runlevel <= runlevel:
                service.start()

    def cleanup(self) -> None:
        "Cleanup services"
        
        for service in reversed(self.services):
            service.cleanup()

    def on_failure(self) -> None:
        "When a critical service crashes"

        logging.critical(
            "Something very bad had occured, cleaning and exiting..."
        )

        self.cleanup()
        os._exit(1)
        
