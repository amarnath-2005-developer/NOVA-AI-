from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime

# Explicitly load from the backend root directory to prevent local fallback
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
load_dotenv(dotenv_path)

import certifi
client = AsyncIOMotorClient(
    os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000
)
db = client[os.getenv("DATABASE_NAME", "nova_ai")]

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_profile: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileRequest(BaseModel):
    email: EmailStr
    profile_name: str

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

@router.post("/register")
async def register_account(req: RegisterRequest):
    collection = db.get_collection("accounts")
    existing = await collection.find_one({"email": req.email})
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    profile_id = req.first_profile.lower().replace(" ", "_")
    
    account = {
        "email": req.email,
        "password_hash": get_password_hash(req.password),
        "profiles": [profile_id],
        "created_at": datetime.now().isoformat()
    }
    
    await collection.insert_one(account)
    
    return {"success": True, "message": "Account created successfully", "profiles": account["profiles"]}

@router.post("/login")
async def login(req: LoginRequest):
    collection = db.get_collection("accounts")
    account = await collection.find_one({"email": req.email})
    
    if not account or not verify_password(req.password, account["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return {
        "success": True, 
        "email": account["email"],
        "profiles": account["profiles"]
    }

@router.post("/profiles")
async def add_profile(req: ProfileRequest):
    collection = db.get_collection("accounts")
    account = await collection.find_one({"email": req.email})
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if len(account.get("profiles", [])) >= 3:
        raise HTTPException(status_code=400, detail="Maximum limit of 3 profiles reached")
        
    profile_id = req.profile_name.lower().replace(" ", "_")
    
    if profile_id in account.get("profiles", []):
        raise HTTPException(status_code=400, detail="Profile already exists")
        
    await collection.update_one(
        {"email": req.email},
        {"$push": {"profiles": profile_id}}
    )
    
    account["profiles"].append(profile_id)
    return {"success": True, "profiles": account["profiles"]}

class PreferencesSyncRequest(BaseModel):
    user_id: str
    preferences: dict

@router.post("/preferences")
async def sync_preferences(req: PreferencesSyncRequest):
    try:
        from app.modules.user.user_manager import UserManager
        um = UserManager()
        for key, val in req.preferences.items():
            await um.update_preferences(req.user_id, key, val)
        return {"success": True, "message": "Preferences synchronized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync preferences: {str(e)}")
