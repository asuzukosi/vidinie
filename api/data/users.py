from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class SubscriptionType(str, Enum):
    FREE = "free"
    PRO = "starter"
    ENTERPRISE = "professional"


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleOAuthVerifiedRequest(BaseModel):
    google_id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdateSubscriptionRequest(BaseModel):
    subscription: SubscriptionType

class UpdateUserRequest(BaseModel):
    email: EmailStr

class User(BaseModel):
    id: str = None
    email: EmailStr
    password: Optional[str] = None  # optional for OAuth users
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_verified: bool = Field(default=False)
    current_subscription: Optional[SubscriptionType] = Field(default=SubscriptionType.FREE)
    profile_picture: Optional[str] = None  # path to profile picture file
    stripe_customer_id: Optional[str] = None  # stripe customer ID
    google_id: Optional[str] = None  # Google user ID for OAuth users

class SafeUser(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    current_subscription: Optional[SubscriptionType]
    profile_picture: Optional[str] = None
    stripe_customer_id: Optional[str] = None

class UserLoginResponse(SafeUser):
    token: str

class UpdateCustomerIdRequest(BaseModel):
    stripe_customer_id: str

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"

class Subscription(BaseModel):
    id: Optional[str] = None
    user_id: str
    stripe_subscription_id: Optional[str] = None  # stripe subscription id
    stripe_price_id: Optional[str] = None  # stripe price id
    subscription_type: SubscriptionType  # free, starter, professional
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)