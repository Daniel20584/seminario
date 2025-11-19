from pydantic import BaseModel
from typing import Optional

class RatingModel(BaseModel):
    user_id: str
    experience_id: str
    comment: Optional[str] = ""
    rating: int
