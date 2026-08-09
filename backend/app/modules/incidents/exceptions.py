class IncidentNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Incident not found")
