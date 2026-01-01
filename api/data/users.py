from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum
from bson import ObjectId

class Subscription(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class RegisterUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    _id: Optional[ObjectId] = None
    username: str
    email: EmailStr
    password: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_verified: bool = Field(default=False)
    current_subscription: Optional[Subscription] = Field(default=Subscription.FREE)

class UserLoginResponse(User):
    token: str

class Payment(BaseModel):
    _id: Optional[ObjectId] = None
    user_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime