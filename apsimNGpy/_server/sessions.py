import socket
import threading
import time
from datetime import datetime, timedelta
from datetime import timezone
from typing import Any, Optional
from typing import Dict
from uuid import uuid4
from datetime import datetime as dtime
from pydantic import BaseModel, Field
import requests
from enum import Enum
from pydantic import BaseModel, ConfigDict
from apsimNGpy import logger
from utils import connect_to_remote_server
from socket import socket


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    STOPPED = "stopped"


class Session(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    session_id: str
    model_name: str
    port: int
    process: Optional[Any] = None
    socket: Optional[socket] = None
    client: Optional[requests.Session] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    last_active: dtime = Field(
        default_factory=lambda: dtime.now(timezone.utc)
    )
    status: SessionStatus = SessionStatus.ACTIVE


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def _get_free_port(self) -> int:
        s = socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def create(self, model_name: str) -> Session:
        session_id = str(uuid4())
        port = self._get_free_port()

        session = Session(
            session_id=session_id,
            model_name=model_name,
            port=port,

        )

        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(f"Session {session_id} not found")
        return session

    def delete(self, session_id: str):
        session = self.get(session_id)

        # 🔥 kill APSIM process if exists
        if session.process:
            session.process.terminate()

        del self.sessions[session_id]

    def touch(self, session_id: str):
        session = self.get(session_id)
        session.last_active = dtime.now(timezone.utc)

    def list(self):
        return list(self.sessions.keys())

    def cleanup_expired(self, timeout_minutes: int = 30):
        now = dtime.now(timezone.utc)
        expired = []

        for session_id, session in self.sessions.items():
            if now - session.last_active > timedelta(minutes=timeout_minutes):
                logger.info(f"⏳ Expiring session {session_id}")
                session.status = SessionStatus.EXPIRED
                expired.append(session_id)

        for session_id in expired:
            logger.info(f"🧹 Cleaning expired session {session_id}")
            self.delete(session_id)


def start_cleanup_task(session_manager, interval=60, timeout=30):
    def cleanup_loop():
        while True:
            time.sleep(interval)
            session_manager.cleanup_expired(timeout_minutes=timeout)

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()


if __name__ == "__main__":
    sm = SessionManager()
    se = sm.create('Maize')
    print(se.session_id)
    # from apsimNGpy import set_apsim_bin_path
    # set_apsim_bin_path(r'C:\Users\rmagala\AppData\Local\Programs\APSIM2026.4.8027.0\bin')
    from apsimNGpy import configuration
    sm.cleanup_expired()
