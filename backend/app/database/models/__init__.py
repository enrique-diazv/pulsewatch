from app.database.base import Base
from app.database.models.user import User

metadata = Base.metadata

__all__ = [
    "User",
    "metadata",
]
