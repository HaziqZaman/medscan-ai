from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user

router = APIRouter()


@router.get("/explain")
def explain(current_user = Depends(get_current_user)):

    return {
        "message": "Explainability endpoint placeholder",
        "user_id": current_user.id
    }