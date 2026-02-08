from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class SubscriptionType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"

class User(BaseModel):
    id: str = None
    email: EmailStr
    password: Optional[str] = None  # optional for OAuth users
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_verified: bool = Field(default=False)
    profile_picture: Optional[str] = None  # path to profile picture file
    stripe_customer_id: Optional[str] = None  # stripe customer ID
    google_id: Optional[str] = None  # Google user ID for OAuth users
    num_videos_left: int = Field(default=2)
