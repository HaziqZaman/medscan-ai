from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/admin/users")
def get_users(current_user = Depends(get_current_user)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "message": "Admin user list placeholder"
    }