from enum import Enum


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    STOPPED = "stopped"
    DELETED = "deleted"
    QUEUED = "queued"


class Session:
    pass
