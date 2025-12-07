from pydantic import BaseModel

class VideoGenerationRequest(BaseModel):
    script: str
    output_path: str

class VideoGenerationResponse(BaseModel):
    video_path: str

class User(BaseModel):
    id: str
    name: str
    email: str
    password: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserLoginResponse(BaseModel):
    token: str

class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class UserRegisterResponse(BaseModel):
    user: User
    token: str

class VideoPipeline(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    status: str
    progress: int
    error: str
    output_path: str
    input_path: str
    output_path: str