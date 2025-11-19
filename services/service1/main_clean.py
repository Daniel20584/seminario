from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
import os

app = FastAPI()

# Configuración de MongoDB
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://experiences-db:27017/experiences_db")
client = MongoClient(DATABASE_URL)
db = client["experiences_db"]
experiences_collection = db["experiences"]


class Experience(BaseModel):
    title: str
    description: str
    price: float
    guide: str


@app.get("/")
def read_root():
    return {"message": "Servicio de experiencias en funcionamiento."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/experiences")
def list_experiences():
    experiences = list(experiences_collection.find({}, {"_id": 0}))
    return {"experiences": experiences}


@app.post("/experiences")
def create_experience(exp: Experience):
    experiences_collection.insert_one(exp.dict())
    return {"msg": "Experiencia creada", "experience": exp}
