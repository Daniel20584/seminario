# Ensure the required package is installed: passlib
# If not installed, run: pip install passlib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from passlib.context import CryptContext
import os

app = FastAPI()

# Configuración de MongoDB
MONGO_URL = os.getenv("DATABASE_URL", "mongodb://auth-db:27017/auth_db")
client = MongoClient(MONGO_URL)
db = client.get_database()
users_collection = db["users"]

# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegister(BaseModel):
    username: str
    password: str
    role: str  # turista, guia, admin

class UserLogin(BaseModel):
    username: str
    password: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register")
def register(user: UserRegister):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    users_collection.insert_one(user_dict)
    return {"msg": "Usuario registrado", "user": user.username, "role": user.role}

@app.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    # Aquí deberías generar un JWT, por ahora solo devolvemos un mensaje
    return {"msg": "Login exitoso", "user": user.username, "role": db_user.get("role", "turista")}
