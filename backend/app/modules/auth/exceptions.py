class EmailAlreadyRegisteredError(Exception):
    def __init__(self) -> None:
        super().__init__("Email is already registered")


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")
