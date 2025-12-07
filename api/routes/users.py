from fastapi import APIRouter
from api.core.models import UserLoginRequest, UserRegisterRequest

router = APIRouter()

@router.post("/login")
async def login(request: UserLoginRequest):
    return {"message": "Login successful"}

@router.post("/register")
async def register(request: UserRegisterRequest):
    return {"message": "Register successful"}


async def get_user(user_id: str):
    pass

async def update_user(user_id: str, request):
    pass

async def delete_user(user_id: str):
    pass

async def update_user_password(user_id: str, request):
    pass

async def get_subscription(user_id: str):
    pass

async def update_subscription(user_id: str, request):
    pass

async def delete_subscription(user_id: str):
    pass

async def get_payment_history(user_id: str):
    pass

async def get_billing_info(user_id: str):
    pass

async def get_all_users():
    pass