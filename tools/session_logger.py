import datetime
import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


class SessionLogger:
    def __init__(self, logs_dir: str | Path = "logs") -> None:
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        self.session_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
        self.file_path = self.logs_dir / f"session-{self.session_id}.log"
        self.log_event("session_start", {"session_id": self.session_id, "started_at": timestamp})

    def _write_line(self, entry: Dict[str, Any]) -> None:
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str, ensure_ascii=False))
            handle.write("\n")

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "payload": payload,
        }
        self._write_line(entry)

    def log_message(self, message: str) -> None:
        self.log_event("message", {"text": message})

    def session_file_path(self) -> str:
        return str(self.file_path.resolve())
