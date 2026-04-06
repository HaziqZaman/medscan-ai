from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel

from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_user
from database.db import get_db
from database import crud

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ----------- Request Schemas -----------

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ----------- Password Helpers -----------

def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


# ----------- Register -----------

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = crud.get_user_by_email(db, data.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(data.password)

    user = crud.create_user(db, email=data.email, password_hash=hashed_password)

    return {
        "message": "User registered successfully",
        "user_id": user.id
    }


# ----------- Login -----------

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = crud.get_user_by_email(db, data.email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ----------- Profile -----------

@router.get("/profile")
def profile(current_user = Depends(get_current_user)):

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }