from pydantic import BaseModel

class Experience(BaseModel):
    title: str
    description: str
    price: float
    guide: str  # Campo obligatorio para identificar al creador
