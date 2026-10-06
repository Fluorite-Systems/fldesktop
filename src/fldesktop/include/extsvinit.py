import subprocess
import threading
import queue
import logging
import time


SERVICES = {
    "udev": {
        "exec": (
            "mkdir -p /run/udev && "
            "udevadm trigger --type=subsystems --action=add && "
            "udevadm trigger --type=devices --action=add && "
            "udevadm settle && exec /usr/lib/systemd/systemd-udevd -N late"
        ),
        "user": 0,
        "depends": [],
    },
    "dbus": {
        "exec": "mkdir -p /var/run/dbus /var/lib/dbus && dbus-uuidgen --ensure 2>/dev/null; exec dbus-daemon --system --nofork",
        "user": 0,
        "depends": ["udev"],
    },
    "bluetooth": {
        "exec": "exec /usr/lib/bluetooth/bluetoothd --nodetach",
        "user": 0,
        "depends": ["dbus"],
    },
    "networkmanager": {
        "exec": "exec /usr/sbin/NetworkManager --no-daemon",
        "user": 0,
        "depends": ["dbus"],
    },
    "cups": {
        "exec": "exec /usr/sbin/cupsd -f",
        "user": 0,
        "depends": ["dbus"],
    },
    "pipewire": {
        "exec": "exec /usr/bin/pipewire",
        "user": 1000,
        "depends": ["dbus"],
    },
    "wireplumber": {
        "exec": "exec /usr/bin/wireplumber",
        "user": 1000,
        "depends": ["pipewire"],
    }
}


class Service:
    def __init__(self, name: str, exec: str = "",
                 user: int = 0, depends: list = []):

        self.name = name
        self.exec = exec
        self.user = user
        self.depends = depends

        self.is_running = False
        self.proc = None

        self.thread = threading.Thread(target=self.supervise)
        self.shutdown = threading.Event()

    def supervise(self):

        self.proc = subprocess.Popen(self.exec, shell=True)

        while not self.shutdown.is_set():
            code = self.proc.poll()
            if code is not None:
                break
            time.sleep(0.1)

        if self.proc.poll() is None:
            self.proc.terminate()

    def start(self):

        if self.thread.is_alive():
            return

        logging.debug(f"Starting external service {self.name}...")

        self.thread.start()

    def stop(self):

        if not self.thread.is_alive():
            return

        logging.debug(f"Stopping external service {self.name}...")

        self.shutdown.set()
        self.thread.join()


class InitWorker:
    def __init__(self):

        self.services = {}

        self.queue = queue.Queue()
        self.stop = threading.Event()

        self.load_services()

    def load_services(self):
        for sv in SERVICES:
            self.services[sv] = Service(sv, **SERVICES[sv])

    def is_running(self):
        for sv in self.services.values():
            if not sv.thread.is_alive():
                return False
        return True

    def full_init(self):

        logging.debug("Starting external services...")

        for sv in self.services.values():
            sv.start()

    def shutdown(self):

        logging.debug("Stopping external services...")

        for sv in self.services.values():
            sv.stop()

    def run_cmd(self, type: str, args: dict):

        match type:
            case "full_init":
                self.full_init()
            case "shutdown":
                self.shutdown()

    def mainloop(self):

        while not self.stop.is_set():
            cmd = self.queue.get()
            self.run_cmd(**cmd)


class ExtSvInit:
    def __init__(self, comm):

        self.comm = comm
        self.comm.register(
            "extsvinit", {
                "full_init": self.full_init,
                "run_service": self.run_service,
                "shutdown": self.shutdown,
                "is_running": self.is_running
            }
        )

        self.worker = InitWorker()
        self.worker_thread = threading.Thread(target=self.worker.mainloop)

        self.worker_thread.start()
        
    def full_init(self):
        logging.debug("full init requested")
        self.worker.queue.put({"type": "full_init", "args": {}})

    def run_service(self, service: str):
        self.worker.queue.put(
            {"type": "run_service", "args": {"service": service}}
        )

    def shutdown(self):
        self.worker.queue.put({"type": "shutdown", "args": {}})
        self.worker.stop.set()

    def is_running(self):
        return self.worker.is_running()