from fastapi import FastAPI, HTTPException
import requests
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

app = FastAPI()

# Configuración de MongoDB
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://reservations-db:27017/reservations_db")
client = MongoClient(DATABASE_URL)
db = client["reservations_db"]
reservations_collection = db["reservations"]

class Reservation(BaseModel):
    id: Optional[str] = None
    experience_id: str
    user_id: str
    date: str
    notes: str = ""
    attended: bool = False
    num_personas: int = 1

@app.get("/")
def root():
    return {"message": "Servicio de reservas en funcionamiento."}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/reservations")
def list_reservations(user_id: Optional[str] = None):
    query = {}
    if user_id:
        query["user_id"] = user_id
    docs = list(reservations_collection.find(query))
    results = []
    for d in docs:
        d["id"] = str(d["_id"])
        del d["_id"]
        results.append(d)
    return results

@app.post("/reservations")
def create_reservation(res: Reservation):
    data = res.dict()
    # Validar fecha
    date_str = data.get("date")
    if not date_str:
        raise HTTPException(status_code=400, detail="Fecha de reserva requerida")
    parsed = None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(date_str, fmt).date()
            break
        except Exception:
            continue
    if not parsed:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    today = datetime.utcnow().date()
    if parsed < today:
        raise HTTPException(status_code=400, detail="No se pueden reservar fechas anteriores a hoy")

    # Validar cupo disponible y descontar cupo real
    experience_id = data.get("experience_id")
    if not experience_id:
        raise HTTPException(status_code=400, detail="ID de experiencia requerido")
    num_personas = int(data.get("num_personas", 1))
    if num_personas < 1:
        num_personas = 1
    EXPERIENCES_URL = os.getenv("EXPERIENCES_SERVICE_URL", "http://experiences-service:8002")
    try:
        resp = requests.get(f"{EXPERIENCES_URL}/experiences/{experience_id}", timeout=5)
        exp_data = resp.json().get("experience")
        cupo = int(exp_data.get("cupo", 1)) if exp_data else 1
    except Exception:
        cupo = 1

    # Sumar el total de personas reservadas para esa experiencia y fecha
    reservas_actuales = 0
    for r in reservations_collection.find({"experience_id": experience_id, "date": date_str}):
        reservas_actuales += int(r.get("num_personas", 1))
    if reservas_actuales + num_personas > cupo:
        raise HTTPException(status_code=400, detail=f"No hay cupos suficientes. Cupo disponible: {cupo - reservas_actuales}")

    # Descontar cupo real en la experiencia
    nuevo_cupo = cupo - num_personas
    if nuevo_cupo < 0:
        nuevo_cupo = 0
    if exp_data:
        exp_data["cupo"] = nuevo_cupo
        # PUT para actualizar el cupo en la experiencia
        try:
            put_resp = requests.put(f"{EXPERIENCES_URL}/experiences/{experience_id}", json=exp_data, timeout=5)
            if put_resp.status_code != 200:
                raise HTTPException(status_code=500, detail="No se pudo actualizar el cupo de la experiencia")
        except Exception:
            raise HTTPException(status_code=500, detail="Error al actualizar el cupo de la experiencia")

    # Ensure attended defaults to False if not provided
    data["attended"] = data.get("attended", False)
    result = reservations_collection.insert_one({k: v for k, v in data.items() if k != "id"})
    data["id"] = str(result.inserted_id)
    return data

@app.get("/reservations/{reservation_id}")
def get_reservation(reservation_id: str):
    reservation = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
    if reservation:
        reservation["id"] = str(reservation["_id"])
        del reservation["_id"]
        return reservation
    return {"error": "Reserva no encontrada"}

@app.put("/reservations/{reservation_id}")
def update_reservation(reservation_id: str, res: Reservation):
    data = res.dict()
    if "id" in data:
        del data["id"]
    result = reservations_collection.update_one({"_id": ObjectId(reservation_id)}, {"$set": data})
    if result.modified_count:
        return {"msg": "Reserva actualizada"}
    return {"error": "No se pudo actualizar la reserva"}


@app.post("/reservations/{reservation_id}/attend")
def mark_attended(reservation_id: str):
    result = reservations_collection.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"attended": True}})
    if result.modified_count:
        return {"msg": "Reserva marcada como asistida"}
    return {"error": "No se pudo marcar asistencia"}

@app.delete("/reservations/{reservation_id}", response_model=dict)
def delete_reservation(reservation_id: str):
    result = reservations_collection.delete_one({"_id": ObjectId(reservation_id)})
    if result.deleted_count:
        return {"msg": "Reserva eliminada"}
    return {"error": "No se pudo eliminar la reserva"}
