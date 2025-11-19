from fastapi import FastAPI
from models import Experience
from pymongo import MongoClient
import os
from bson.objectid import ObjectId

app = FastAPI()

# Configuración de MongoDB
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://experiences-db:27017/experiences_db")
client = MongoClient(DATABASE_URL)
db = client["experiences_db"]
experiences_collection = db["experiences"]




@app.get("/")
def read_root():
    return {"message": "Servicio de experiencias en funcionamiento."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/experiences")
def list_experiences(guide: str = None):
    if guide:
        experiences = list(experiences_collection.find({"guide": guide}))
    else:
        experiences = list(experiences_collection.find({}))
    # Convertir _id a id (string) en cada experiencia
    for exp in experiences:
        exp["id"] = str(exp["_id"])
        del exp["_id"]
    return {"experiences": experiences}


@app.post("/experiences")
def create_experience(exp: Experience):
    experiences_collection.insert_one(exp.dict())
    return {"msg": "Experiencia creada", "experience": exp}


@app.get("/experiences/{exp_id}")
def get_experience(exp_id: str):
    experience = experiences_collection.find_one({"_id": ObjectId(exp_id)})
    if experience:
        experience["id"] = str(experience["_id"])
        del experience["_id"]
        return {"experience": experience}
    return {"error": "Experiencia no encontrada"}, 404


@app.put("/experiences/{exp_id}")
def update_experience(exp_id: str, exp: Experience):
    result = experiences_collection.update_one(
        {"_id": ObjectId(exp_id)},
        {"$set": exp.dict()}
    )
    if result.modified_count:
        return {"msg": "Experiencia actualizada"}
    return {"error": "No se pudo actualizar la experiencia"}, 404


@app.delete("/experiences/{exp_id}")
def delete_experience(exp_id: str):
    result = experiences_collection.delete_one({"_id": ObjectId(exp_id)})
    if result.deleted_count:
        return {"msg": "Experiencia eliminada"}
    return {"error": "No se pudo eliminar la experiencia"}, 404
