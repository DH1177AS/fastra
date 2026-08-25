import json, os, hmac, hashlib
from datetime import datetime
from pathlib import Path

class SecureAuditLog:
    def __init__(self, log_path: str, secret_key: str):
        self.log_path = Path(log_path)
        self.secret_key = secret_key.encode()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("")

    def _hmac(self, data: str) -> str:
        return hmac.new(self.secret_key, data.encode(), hashlib.sha256).hexdigest()

    def add_entry(self, user: str, action: str, details: dict):
        prev_hash = ""
        if self.log_path.stat().st_size > 0:
            with open(self.log_path, "rb") as f:
                try:
                    f.seek(-2, 2)
                    while f.read(1) != b'\n':
                        f.seek(-2, 1)
                except OSError:
                    f.seek(0)
                last_line = f.readline().decode().strip()
                if last_line:
                    prev_hash = json.loads(last_line).get("current_hash", "")

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "action": action,
            "details": details,
            "previous_hash": prev_hash,
        }
        entry["current_hash"] = self._hmac(json.dumps(entry, sort_keys=True, ensure_ascii=False))
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def verify_integrity(self) -> bool:
        if not self.log_path.exists():
            return True
        with open(self.log_path, "r") as f:
            lines = f.readlines()
        for i in range(1, len(lines)):
            prev = json.loads(lines[i-1])
            curr = json.loads(lines[i])
            if prev.get("current_hash") != curr.get("previous_hash"):
                return False
        return True