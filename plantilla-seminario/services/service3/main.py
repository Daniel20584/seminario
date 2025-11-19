from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# FastAPI app
app = FastAPI()

# MongoDB connection
MONGO_DETAILS = "mongodb://mongo:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.ratings_db
ratings_collection = db.get_collection("ratings")

# Pydantic models
class Rating(BaseModel):
    user_id: str
    experience_id: str
    comment: str
    rating: int

class RatingResponse(Rating):
    id: str

# Helper function to serialize MongoDB documents
def rating_helper(rating) -> dict:
    return {
        "id": str(rating["_id"]),
        "user_id": rating["user_id"],
        "experience_id": rating["experience_id"],
        "comment": rating["comment"],
        "rating": rating["rating"],
    }

# Routes
@app.post("/ratings", response_model=RatingResponse)
async def create_rating(rating: Rating):
    new_rating = await ratings_collection.insert_one(rating.dict())
    created_rating = await ratings_collection.find_one({"_id": new_rating.inserted_id})
    return rating_helper(created_rating)

@app.get("/ratings", response_model=List[RatingResponse])
async def get_ratings():
    ratings = []
    async for rating in ratings_collection.find():
        ratings.append(rating_helper(rating))
    return ratings

@app.get("/ratings/{id}", response_model=RatingResponse)
async def get_rating(id: str):
    rating = await ratings_collection.find_one({"_id": ObjectId(id)})
    if rating:
        return rating_helper(rating)
    raise HTTPException(status_code=404, detail="Rating not found")

@app.delete("/ratings/{id}")
async def delete_rating(id: str):
    delete_result = await ratings_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return {"message": "Rating deleted successfully"}
    raise HTTPException(status_code=404, detail="Rating not found")

@app.get("/health")
def health():
    return {"status": "ok"}
