from pydantic import BaseModel, Field


class RealtimeTicketResponse(BaseModel):
    ticket: str = Field(min_length=32)
    expires_in: int = Field(gt=0)
