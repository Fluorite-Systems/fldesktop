import json
import os
import hashlib
import base64


class LoginManager:
    def __init__(self, comm) -> None:

        self.comm = comm
        self.comm.register(
            "loginmgr", {
                "is_available": self.check_availability,
                "check_password": self.check_password
            }
        )

        self.file_path = self.comm.request("osmgr", "get_path", "login.json")

    def read_file(self) -> dict | None:
        "Read login.json"

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except:
            return None
            
        return data

    def check_availability(self, data: dict = None) -> bool:
        "Can we log in?"

        data = data if data else self.read_file()

        if data and type(data) == dict:
            if "pwhash" in data:
                return True

        return False

    def check_password(self, password: str):
        "Check password by its hash from login.json"

        data = self.read_file()
        if self.check_availability(data):
            
            parts = data["pwhash"].split("$")

            if len(parts) != 4:
                raise ValueError("Неверный формат хеша")
            
            _, iterations_str, salt_b64, stored_hash_b64 = parts
            
            iterations = int(iterations_str)
            salt = base64.b64decode(salt_b64)
            stored_hash = base64.b64decode(stored_hash_b64)

            hash_bytes = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations,
                dklen=len(stored_hash)
            )
            
            return hash_bytes == stored_hash

        return False
