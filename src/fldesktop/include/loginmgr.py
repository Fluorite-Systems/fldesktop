import json
import os
import hashlib
import base64


class LoginManager:
    def __init__(self, comm) -> None:

        self.comm = comm
        self.comm.register(
            "loginmgr", {
                "check_password": self.check_password
            }
        )

    def check_availability(self) -> bool:
        "Can we log in?"

        return bool(self.comm.request("cfgmgr", "get", "pwhash"))

    def check_password(self, password: str) -> bool:
        "Check password by its hash from login.json"

        if self.check_availability():
            hash = self.comm.request("cfgmgr", "get", "auth-pwhash") 
            parts = hash.split("$")

            if len(parts) != 4:
                return False

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
