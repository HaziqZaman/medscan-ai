from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user

router = APIRouter()


@router.post("/chatbot")
def chatbot(message: str, current_user = Depends(get_current_user)):

    return {
        "user_id": current_user.id,
        "response": "Chatbot response placeholder"
    }