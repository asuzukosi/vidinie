from fastapi import APIRouter, HTTPException, Depends
from api.data.users import User, SafeUser, RegisterUserRequest, \
                        LoginUserRequest, UserLoginResponse
from api.core.db import users_collection
from bson.objectid import ObjectId
from api.core.auth import get_hashed_password, verify_password, signJWT, JWTBearer
from utils.logger import get_logger
logger = get_logger("users")
router = APIRouter(tags=["users"])

@router.post("/register")
async def register(request: RegisterUserRequest) -> SafeUser:
    user = await users_collection.find_one({"email": request.email})
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # hash password
    hashed_password = get_hashed_password(request.password)
    # create user object
    user = User(username=request.username, 
                email=request.email, 
                password=hashed_password)
    # insert user into database
    db_user = await users_collection.insert_one(user.model_dump(mode="json"))
    # update user id
    await users_collection.update_one(
        {"_id": db_user.inserted_id},
        {"$set": {"id": str(db_user.inserted_id)}}
    )
    # return user
    user.id = str(db_user.inserted_id)
    return SafeUser(**user.model_dump(mode="json"), exclude={"password"})

@router.post("/login")
async def login(request: LoginUserRequest) -> User:
    user = await users_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = signJWT(user["id"])
    return UserLoginResponse(**user, token=token)

@router.get("/me", dependencies=[Depends(JWTBearer())])
async def me(user_id: str = Depends(JWTBearer())) -> User:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)
