from fastapi import APIRouter, HTTPException

# Updated imports pointing to the new folders
from app.models.schemas import UserCreate, UserLogin
from app.services.session_manager import create_user, get_user, authenticate_user

# (auth.py is still in your root Backend folder)
from app.core.auth import get_password_hash

router = APIRouter(tags=["Authentication"])

@router.post("/register")
async def register_user(user: UserCreate):
    db_user = get_user(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    create_user(user.email, hashed_password, user.name)
    return {"message": "User created successfully"}

@router.post("/login")
async def login_for_access_token(user: UserLogin):
    authenticated_user = authenticate_user(user.email, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": user.email, "token_type": "bearer", "user_name": authenticated_user['name']}