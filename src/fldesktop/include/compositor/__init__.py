import json
import socket
import os
import uuid
import threading
import logging
import msgpack
import struct
from typing import Optional


class ClientHandler:
    def __init__(self, connection: socket.socket, client_address: str, comm):
        self.connection = connection
        self.client_address = client_address
        self.comm = comm
        self.callback = self.handle_callback
        self.is_active = True
        self.uuid = None
        self.thread = None
        self.data_fmt = "json"
    
    def handle_callback(self, s: str | dict):

        logging.debug(f"Handling callback: {s}")

        if isinstance(s, dict):
            if self.data_fmt == "msgpack":
                s = msgpack.dumps(s)
            else:
                s = json.dumps(s).encode("utf-8")
        else:
            s = s.encode("utf-8")

        if s == b"close":
            self.close()
            return

        try:
            message_length = len(s)
            length_prefix = struct.pack(">I", message_length)
            self.connection.sendall(length_prefix + s)
        except (BrokenPipeError, OSError) as e:
            logging.error(
                f"Failed to send data to {self.client_address}: {e}"
            )
            self.close()
    
    def handle_client(self):
        "Client handling logics"

        logging.info("New client connected")
        
        try:
            while self.is_active:

                size_data = self.connection.recv(4, socket.MSG_WAITALL)
                
                if not size_data or len(size_data) < 4:
                    break

                size = struct.unpack(">I", size_data)[0]

                data = self.connection.recv(size, socket.MSG_WAITALL)
                
                if len(data) < size:
                    break

                self.process_message(data)

        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            logging.error(
                f"Error processing client {self.client_address}: {e}"
            )
        finally:
            self.close()
    
    def process_message(self, message: bytes):
        "Process incoming message"

        if message.strip()[0] == 0x7b:
            data = json.loads(message.decode('utf-8').strip())
            self.data_fmt = "json"
        else:
            data = msgpack.unpackb(message, strict_map_key=False)
            self.data_fmt = "msgpack"

        if "type" in data:
            if data["type"] == "init_client":
                # Create a window
                uuid4 = str(uuid.uuid4())
                self.uuid = uuid4

                title = data["title"] if "title" in data else \
                    self.comm.request(
                        "localemgr", "tr", "Unnamed application"
                    )
                package = data["package"] if "package" in data else "none"
                wsize = (
                    int(data["width"]) if "width" in data else 500,
                    int(data["height"]) if "height" in data else 400
                )
                wtype = data["windowtype"] if "windowtype" in data else \
                                                                "normal"

                self.comm.request(
                    "clientmgr", "new_client",
                    uuid4, title, package,
                    wsize, wtype, self.callback
                )

                self.callback({"uuid": uuid4})
            else:
                if "uuid" in data:
                    self.comm.request(
                        "clientmgr", "notify_client", data["uuid"], data
                    )
    
    def close(self):
        "Close client connection"
        if not self.is_active:
            return
            
        self.is_active = False
        
        self.comm.request("clientmgr", "kill_client", self.uuid)
        
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.connection.close()
        except:
            pass
            
        logging.info(f"Client {self.uuid} disconnected")


class AppServer:
    def __init__(self, comm):
        self.comm = comm
        self.comm.register("appserver", {"stop": self.stop})
            
        self.socket_path = os.path.join(
            os.environ["XDG_RUNTIME_DIR"], "flos.socket"
        )
        
        self.server_socket: Optional[socket.socket] = None

        self._stop_event = threading.Event()
        self._client_handlers = []
        self.server_thread = threading.Thread(
            target=self.start,
            name="AppServer",
            daemon=False
        )
        self.server_thread.start()
    
    def start(self):
        "Start server"
        try:
            os.unlink(self.socket_path)
        except OSError:
            if os.path.exists(self.socket_path):
                raise

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        logging.info(f"Appserver started at {self.socket_path}")

        self.server_socket.settimeout(1.0)

        while not self._stop_event.is_set():
            try:
                connection, client_address = self.server_socket.accept()
                logging.info("Accepted a new client")

                handler = ClientHandler(connection, client_address, self.comm)
                client_thread = threading.Thread(
                    target=handler.handle_client,
                    daemon=False
                )
                handler.thread = client_thread
                client_thread.start()
                self._client_handlers.append(handler)
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"Ошибка сервера: {e}")
                break

    def stop(self):
        "Stop server"

        logging.info("Stopping server...")
        self._stop_event.set()

        # Close client handlers
        for handler in self._client_handlers:
            try:
                handler.close()
            except Exception as e:
                logging.error(f"An error occured while closing a client: {e}")

        for handler in self._client_handlers:
            if handler.thread and handler.thread.is_alive():
                handler.thread.join(timeout=2.0)
                if handler.thread.is_alive():
                    logging.error("Client thread was not stopped")

        # Close and unlink server socket
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.server_socket.close()
            except:
                pass

        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
                logging.info("Socket file deleted")
        except Exception as e:
            logging.critical(f"Failed to delete socket file: {e}")

        logging.info("Appserver stopped")

    def srv_cleanup(self):
        "Service cleanup method for Init"

        self.stop()
