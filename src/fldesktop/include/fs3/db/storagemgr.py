from pathlib import Path
import msgpack


class StorageManager:
    def __init__(self, db, path):

        self.db = db

        self.workdir_path = Path(path)
        self.wal_path = self.workdir_path / "wal"

        self.prepare()

    def prepare(self) -> None:
        "Prepare working dir and files"

        if not self.workdir_path.exists():
            self.workdir_path.mkdir(parents=True, exist_ok=True)
            self.wal_path.touch()

    def load(self) -> None:
        "Load transactions from WAL"

        with open(self.wal_path, "r+b") as f:
            unpacker = msgpack.Unpacker(f, raw=False)
            for tr in unpacker:
                if isinstance(tr, dict):
                    tr["wal_load"] = True
                    self.db.run_transaction(**tr)

    def append(self, tr) -> None:
        "Append WAL by one transaction"

        with open(self.wal_path, "a+b") as f:
            f.write(msgpack.dumps(tr))