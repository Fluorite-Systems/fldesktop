import json
import socket
import os
import uuid
import threading
import logging
from typing import Optional


class ClientHandler:
    def __init__(self, connection: socket.socket, client_address: str, comm):
        self.connection = connection
        self.client_address = client_address
        self.comm = comm
        self.callback = self.handle_callback
        self.is_active = True
        self.uuids = []
        self.thread = None
    
    def handle_callback(self, s: str):

        logging.debug(f"Handling callback: {s}")

        if s == "close":
            self.close()
        else:
            try:
                self.connection.sendall((s + "\x00").encode("utf-8"))
            except (BrokenPipeError, OSError):
                self.close()
    
    def handle_client(self):
        "Client handling logics"

        logging.info("New client connected")
        
        try:
            while self.is_active:
                # Receive some chunks from client and join them
                chunks = []

                while True:
                    data = self.connection.recv(1024)
                    chunks.append(data)
                    if b"\x00" in data:
                        break

                    if not data:
                        chunks = None
                        break

                if chunks == None:
                    break
                
                data = b"".join(chunks)
                message = data.decode('utf-8').strip()

                # Process message and respond to it
                response = self.process_message(message)

                if type(response) == str and response:
                    try:
                        self.connection.sendall((response + "\x00").encode('utf-8'))
                    except (BrokenPipeError, OSError):
                        break

        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            logging.error(f"Error processing client {self.client_address}: {e}")
        finally:
            self.close()
    
    def process_message(self, raw_message: str) -> str:
        "Process incoming message"

        for message in raw_message.split("\x00"):
            if not message:
                continue
                
            data = json.loads(message)

            if "type" in data:
                if data["type"] == "create_window":
                    # Create a window
                    uuid4 = str(uuid.uuid4())
                    self.uuids.append(uuid4)
                    self.comm.request("clientmgr", "new_client",
                                    data["payload"]["title"], 
                                    data["payload"]["package"],
                                    uuid4, self.callback)

                    return '{"uuid": "' + uuid4 + '"}'
                else:
                    if "uuid" in data:
                        self.comm.send(
                            "clientmgr", "notify_client", data["uuid"], data
                        )

                    return None
            
        
        return "nothing"
    
    def close(self):
        "Close client connection"
        if not self.is_active:
            return
            
        self.is_active = False
        
        for uuid_client in self.uuids:
            self.comm.send("clientmgr", "kill_client", uuid_client)
        
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.connection.close()
        except:
            pass
            
        logging.info(f"Client with {self.uuids[0]} windows disconnected")


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
