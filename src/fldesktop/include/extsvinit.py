import subprocess
import threading
import queue
import logging
import time
import signal
import os


SERVICES = {
    "udev": {
        "exec": (
            "mkdir -p /run/udev && "
            "/usr/lib/systemd/systemd-udevd --daemon && "
            "while [ ! -S /run/udev/control ]; do sleep 0.1; done && "
            "udevadm trigger --type=subsystems --action=add && "
            "udevadm trigger --type=devices --action=add && "
            "udevadm settle && "
            "udevadm control --exit && "
            "sleep 0.5 && "
            "exec /usr/lib/systemd/systemd-udevd -N late"
        ),
        "wait": "while [ ! -S /run/udev/control ]; do sleep 0.05; done",
        "user": 0
    },
    "seatd": {
        "exec": "exec /usr/sbin/seatd -g seatd",
        "wait": "while [ ! -S /run/seatd.sock ]; do sleep 0.05; done",
        "user": 0
    },
    "cage": {
        "exec": (
            "export XDG_RUNTIME_DIR=/run/user/1000 && "
            "exec cage -- sleep infinity"
        ),
        "wait": "while [ ! -S /run/user/1000/wayland-0 ]; do sleep 0.05; done",
        "user": 1000
    },
    "dbus": {
        "exec": "mkdir -p /var/run/dbus /var/lib/dbus && dbus-uuidgen --ensure 2>/dev/null; exec dbus-daemon --system --nofork",
        "wait": "while [ ! -S /run/dbus/system_bus_socket ]; do sleep 0.05; done",
        "user": 0
    },
    "bluetooth": {
        "exec": "exec /usr/lib/bluetooth/bluetoothd --nodetach",
        "wait": "while [ ! -S /run/dbus/system_bus_socket ]; do sleep 0.05; done",
        "user": 0
    },
    "networkmanager": {
        "exec": "exec /usr/sbin/NetworkManager --no-daemon",
        "wait": "while [ ! -S /run/dbus/system_bus_socket ]; do sleep 0.05; done",
        "user": 0
    },
    "cups": {
        "exec": "exec /usr/sbin/cupsd -f",
        "wait": "while [ ! -S /run/cups/cups.sock ]; do sleep 0.05; done",
        "user": 0
    },
    "pipewire": {
        "exec": (
            "export XDG_RUNTIME_DIR=/run/user/1000 && "
            "mkdir -p $XDG_RUNTIME_DIR && "
            "chmod 0700 $XDG_RUNTIME_DIR && "
            "chown 1000:1000 $XDG_RUNTIME_DIR && "
            "exec dbus-run-session -- pipewire"
        ),
        "wait": "while [ ! -S /run/user/1000/pipewire-0 ]; do sleep 0.05; done",
        "user": 1000
    },
    "wireplumber": {
        "exec": "exec /usr/bin/wireplumber",
        "wait": "while [ ! -S /run/user/1000/pipewire-0 ]; do sleep 0.05; done",
        "user": 1000
    }
}


class Service:
    def __init__(self, name: str, exec: str = "", wait: str = "",
                 user: int = 0):

        self.name = name
        self.exec = exec
        self.wait = wait
        self.user = user

        self.proc = None
        self.is_running = False
        self.is_ready = False

        self.thread = threading.Thread(target=self.supervise)
        self.shutdown = threading.Event()

    def _wrap(self, cmd: str) -> str:
        if self.user != 0 and os.getuid() != self.user:
            return (
                f"setpriv --reuid={self.user} --regid={self.user} "
                f"--init-groups --inh-caps=-all -- "
                f"/bin/sh -c {self._quote(cmd)}"
            )
        return cmd

    @staticmethod
    def _quote(s: str) -> str:
        return "'" + s.replace("'", "'\\''") + "'"

    def _log_stream(self, stream, level: int):
        for line in iter(stream.readline, b""):
            text = line.decode(errors="replace").rstrip()
            if text:
                logging.log(level, f"[{self.name}] {text}")

    def supervise(self):

        while not self.shutdown.is_set():

            try:
                self.proc = subprocess.Popen(
                    self._wrap(self.exec),
                    shell=True,
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except Exception:
                logging.exception(f"[{self.name}] failed to spawn")
                if self.shutdown.wait(1):
                    break
                continue

            self.is_running = True

            log_thread = threading.Thread(
                target=self._log_stream,
                args=(self.proc.stdout, logging.INFO),
                daemon=True,
            )
            log_thread.start()

            while not self.shutdown.is_set():
                if self.proc.poll() is not None:
                    break
                time.sleep(0.1)

            self.is_running = False

            if self.shutdown.is_set():
                break

            logging.warning(
                f"[{self.name}] exited with code {self.proc.returncode}, restarting"
            )
            if self.shutdown.wait(1):
                break

        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass

    def wait_ready(self):

        if not self.wait:
            self.is_ready = True
            return

        while not self.shutdown.is_set():
            try:
                r = subprocess.run(
                    self._wrap(self.wait),
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except Exception:
                logging.exception(f"[{self.name}] wait spawn failed")
                if self.shutdown.wait(1):
                    return
                continue

            if r.returncode == 0:
                self.is_ready = True
                return

            out = r.stdout.decode(errors="replace").rstrip()
            logging.warning(
                f"[{self.name}] wait failed rc={r.returncode} {out!r}, retrying"
            )
            if self.shutdown.wait(1):
                return

    def start(self, blocking: bool = True):

        if self.thread.is_alive():
            return

        logging.debug(f"Starting external service {self.name}...")

        self.shutdown.clear()
        self.is_ready = False
        self.thread.start()

        if blocking:
            self.wait_ready()

    def stop(self):

        if not self.thread.is_alive():
            return

        logging.debug(f"Stopping external service {self.name}...")

        self.shutdown.set()

        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

        self.thread.join(timeout=10)


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
            sv.start(blocking=False)

    def run_service(self, name):

        svc = self.services.get(name)
        if svc is None:
            logging.warning(f"Unknown service: {name}")
            return
        svc.start(blocking=True)

    def shutdown(self):

        logging.debug("Stopping external services...")

        for sv in self.services.values():
            sv.stop()

        self.stop.set()

    def run_cmd(self, type: str, args: dict, result: dict):

        try:
            match type:
                case "full_init":
                    self.full_init()
                case "run_service":
                    self.run_service(args["service"])
                case "shutdown":
                    self.shutdown()
            result["ok"] = True
        except Exception as e:
            logging.exception(f"Command failed: {type}")
            result["ok"] = False
            result["error"] = e
        finally:
            result["event"].set()

    def mainloop(self):

        while not self.stop.is_set():
            try:
                cmd = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
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

    def _submit(self, type: str, args: dict) -> bool:
        result = {"ok": False, "error": None, "event": threading.Event()}
        self.worker.queue.put({
            "type": type,
            "args": args,
            "result": result,
        })
        result["event"].wait()
        if not result["ok"]:
            raise result["error"]
        return True

    def full_init(self):
        logging.debug("full init requested")
        self.worker.queue.put(
            {
                "type": "full_init",
                "args": {},
                "result": {
                    "ok": False,
                    "error": None,
                    "event": threading.Event()
                }
            }
        )

    def run_service(self, service: str):
        return self._submit("run_service", {"service": service})

    def shutdown(self):
        self.worker.queue.put(
            {
                "type": "shutdown",
                "args": {},
                "result": {
                    "ok": False,
                    "error": None,
                    "event": threading.Event()
                }
            }
        )

    def is_running(self):
        return self.worker.is_running()