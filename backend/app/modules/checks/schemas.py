from typing import Literal

from pydantic import BaseModel, Field


class CheckQueuedResponse(BaseModel):
    task_id: str = Field(min_length=1)
    status: Literal["queued"] = "queued"
