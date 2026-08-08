class MonitorNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Monitor not found")
