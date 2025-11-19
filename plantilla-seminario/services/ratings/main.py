from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = FastAPI()

# Configuración de MongoDB
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://ratings-db:27017/ratings_db")
client = MongoClient(DATABASE_URL)
db = client["ratings_db"]
ratings_collection = db["ratings"]

class Rating(BaseModel):
    id: Optional[str] = None
    experience_id: str
    user_id: str
    username: str
    comment: str = ""
    rating: int

@app.post("/ratings")
def create_rating(r: Rating):
    data = r.dict()
    result = ratings_collection.insert_one({k: v for k, v in data.items() if k != "id"})
    data["id"] = str(result.inserted_id)
    return data

@app.get("/ratings")
def list_ratings(experience_id: Optional[str] = None, guide: Optional[str] = None):
    query = {}
    if experience_id:
        query["experience_id"] = experience_id
    docs = list(ratings_collection.find(query))
    results = []
    for d in docs:
        d["id"] = str(d["_id"])
        del d["_id"]
        results.append(d)
    return results

@app.get("/ratings/guide/{guide}")
def ratings_for_guide(guide: str):
    # Aquí deberías consultar las experiencias del guía y filtrar las valoraciones
    # Este endpoint se puede mejorar integrando con el servicio de experiencias
    return {"msg": "Endpoint para ver valoraciones de reservas por guía"}
