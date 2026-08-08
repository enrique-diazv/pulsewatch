from enum import StrEnum


class MonitorStatus(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    UNKNOWN = "UNKNOWN"


class HttpMethod(StrEnum):
    GET = "GET"
