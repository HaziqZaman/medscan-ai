from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }