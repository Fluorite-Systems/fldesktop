from fldesktop.include import (communicator, desktop, dialogs,
                     thememgr, pkgmgr, lockscreen, os_manager,
                     configmgr, compositor, search, wm, loginmgr,
                     localemgr, notifications, iconmgr, QApp,
                     PostInit)
from fldesktop.include.compositor.clientmgr import ClientManager
from fldesktop.include.widgets.surface import SurfaceManager
from fldesktop.include.input import InputManager

import logging
import os


SERVICES = {
    "OSManager": {
        "object": os_manager.OSManager,
        "importance": "critical"
    },
    "ConfigManager": {
        "object": configmgr.ConfigurationManager,
        "importance": "critical",
        "depends": ["QApplication", "OSManager"]
    },
    "LocaleManager": {
        "object": localemgr.LocaleManager,
        "importance": "critical",
        "depends": ["ConfigManager"]
    },
    "PackageManager": {
        "object": pkgmgr.PackageManager,
        "depends": ["QApplication"]
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
        "depends": ["QApplication"]
    },
    "Desktop": {
        "object": desktop.Desktop,
        "importance": "critical",
        "depends": [
            "QApplication", "ConfigManager",
            "IconManager", "PackageManager",
            "SurfaceManager", "InputManager"
        ]
    },
    "QApplication": {
        "object": QApp,
        "importance": "critical"
    },
    "IconManager": {
        "object": iconmgr.IconManager,
        "importance": "critical",
        "depends": ["QApplication", "ThemingManager"]
    },
    "ThemingManager": {
        "object": thememgr.ThemingManager,
        "importance": "critical",
        "depends": ["QApplication"]
    },
    "WindowManager": {
        "object": wm.WindowManager,
        "importance": "critical",
        "depends": ["Desktop"]
    },
    "AppServer": {
        "object": compositor.AppServer,
        "depends": ["WindowManager"]
    },
    "ClientManager": {
        "object": ClientManager,
        "depends": ["AppServer"]
    },
    "Lockscreen": {
        "object": lockscreen.LockScreen,
        "depends": ["LoginManager", "Desktop"]
    },
    "NotifyManager": {
        "object": notifications.NotificationManager,
        "depends": ["Desktop"]
    },
    "DialogManager": {
        "object": dialogs.DialogManager,
        "depends": ["WindowManager"]
    },
    "PostInit": {
        "object": PostInit,
        "depends": ["QApplication"]
    },
    "QtEventLoop": {
        "object": QApp.exec,
        "importance": "critical",
        "restart": True,
        "depends": ["QApplication"]
    }
}


DEFAULTS = [
    ("object", lambda: ...), ("importance", "optional"),
    ("depends", []), ("restart", False)
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

        logging.info(f"Starting service {self.name}")

        try:
            self.object = self.object(self.comm)
        except Exception as e:
            logging.critical(f"Service {self.name} failed: {e}")

            if self.restart:
                self.start()

            if self.importance == "critical":
                self.comm.send("init", "failure")
        else:
            self.started = True

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
                
    def run(self) -> None:
        "Start services"

        logging.info("Starting services...")
        
        for service in self.services:
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
        
