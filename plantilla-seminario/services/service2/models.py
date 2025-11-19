from pydantic import BaseModel
from typing import Optional

class ReservationModel(BaseModel):
    experience_id: str
    user_id: str
    date: str
    notes: Optional[str] = ""
