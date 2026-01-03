from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum
from bson import ObjectId

class Subscription(str, Enum):
    FREE = "free"
    PRO = "starter"
    ENTERPRISE = "professional"


class RegisterUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UpdateSubscriptionRequest(BaseModel):
    subscription: Subscription

class User(BaseModel):
    id: str = None
    username: str
    email: EmailStr
    password: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_verified: bool = Field(default=False)
    current_subscription: Optional[Subscription] = Field(default=Subscription.FREE)
    profile_picture: Optional[str] = None  # path to profile picture file
    stripe_customer_id: Optional[str] = None  # stripe customer ID

class SafeUser(BaseModel):
    id: str
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    current_subscription: Optional[Subscription]
    profile_picture: Optional[str] = None
    stripe_customer_id: Optional[str] = None

class UserLoginResponse(SafeUser):
    token: str

class Payment(BaseModel):
    _id: Optional[ObjectId] = None
    user_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

class PaymentMethodCard(BaseModel):
    brand: str  # e.g., "visa", "mastercard", "amex"
    last4: str
    exp_month: int
    exp_year: int

class PaymentMethod(BaseModel):
    id: Optional[str] = None
    _id: Optional[ObjectId] = None
    user_id: str
    stripe_payment_method_id: str  # Stripe payment method ID
    type: str = "card"  # payment method type
    card: Optional[PaymentMethodCard] = None
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CreatePaymentMethodRequest(BaseModel):
    stripe_payment_method_id: str
    type: str = "card"
    card: Optional[PaymentMethodCard] = None
    is_default: bool = False

class UpdatePaymentMethodRequest(BaseModel):
    is_default: Optional[bool] = None
    card: Optional[PaymentMethodCard] = None

class UpdateCustomerIdRequest(BaseModel):
    stripe_customer_id: str

class PaymentMethodResponse(BaseModel):
    id: str
    user_id: str
    stripe_payment_method_id: str
    type: str
    card: Optional[PaymentMethodCard] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime