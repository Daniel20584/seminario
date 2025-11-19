from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = FastAPI()

# Configuración de MongoDB
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://reservations-db:27017/reservations_db")
client = MongoClient(DATABASE_URL)
db = client["reservations_db"]
reservations_collection = db["reservations"]

class Reservation(BaseModel):
    experience_id: str
    user_id: str
    date: str
    notes: str = ""

@app.get("/")
def root():
    return {"message": "Servicio de reservas en funcionamiento."}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/reservations", response_model=List[Reservation])
def list_reservations():
    reservations = list(reservations_collection.find({}, {"_id": 0}))
    return reservations

@app.post("/reservations", response_model=Reservation)
def create_reservation(res: Reservation):
    reservations_collection.insert_one(res.dict())
    return res

@app.get("/reservations/{reservation_id}", response_model=Reservation)
def get_reservation(reservation_id: str):
    reservation = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
    if reservation:
        reservation["id"] = str(reservation["_id"])
        del reservation["_id"]
        return reservation
    return {"error": "Reserva no encontrada"}

@app.put("/reservations/{reservation_id}", response_model=dict)
def update_reservation(reservation_id: str, res: Reservation):
    result = reservations_collection.update_one({"_id": ObjectId(reservation_id)}, {"$set": res.dict()})
    if result.modified_count:
        return {"msg": "Reserva actualizada"}
    return {"error": "No se pudo actualizar la reserva"}

@app.delete("/reservations/{reservation_id}", response_model=dict)
def delete_reservation(reservation_id: str):
    result = reservations_collection.delete_one({"_id": ObjectId(reservation_id)})
    if result.deleted_count:
        return {"msg": "Reserva eliminada"}
    return {"error": "No se pudo eliminar la reserva"}
