from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import verify_password, create_access_token

# Updated imports pointing to the new folders
from app.models.schemas import UserCreate, UserLogin
from app.services.session_manager import create_user, get_user, authenticate_user
from app.core.auth import get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register_user(user: UserCreate):
    db_user = get_user(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    create_user(user.email, hashed_password, user.name)
    
    return {"message": "User created successfully"}

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Fetch the user from your database using session_manager
    user = get_user(form_data.username)
    
    # 2. Verify the user exists and the password is correct
    # Note: If your get_user returns an object instead of a dict, use user.hashed_password
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Generate the JWT
    access_token = create_access_token(data={"sub": user["email"]})
    
    # 4. Return the token and the user's name to the frontend
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_name": user["name"]
    }