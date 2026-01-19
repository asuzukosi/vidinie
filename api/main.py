from fastapi import FastAPI
from api.routes import users, pipelines
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from api.core.signals import connect_to_broadcast, disconnect_from_broadcast
from api.core.config import initialize_config, destroy_config
from api.core.db import initialize_db, disconnect_from_db
from core.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

# define application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize the configuration
    await initialize_config()
    # initialize the database
    await initialize_db()
    # connect to the broadcast server
    await connect_to_broadcast()

    yield
    # disconnect from the broadcast server
    await disconnect_from_broadcast()
    # disconnect from the database
    await disconnect_from_db()
    # destroy the configuration
    await destroy_config()

# create the fastapi app
app = FastAPI(title="[vidinie] backend service api",
               description="API for Vidinie",
               version="0.1.0",
               openapi_url="/openapi.json",
               lifespan=lifespan)
# add cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3000/", 
                   "https://vidinie.com", "https://api.vidinie.com"] + [os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# custom static file handler with cors headers
class CORSStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            if message["type"] == "http.response.start":
                # add cors headers to static file responses
                headers = dict(message.get("headers", []))
                headers[b"access-control-allow-origin"] = f"{frontend_url}".encode("utf-8")
                headers[b"access-control-allow-credentials"] = b"true"
                headers[b"access-control-allow-methods"] = b"*"
                headers[b"access-control-allow-headers"] = b"*"
                message["headers"] = list(headers.items())
            await send(message)
        
        await super().__call__(scope, receive, send_wrapper)

# mount the media directory
if not os.path.exists("temp"):
    os.makedirs("temp", exist_ok=True)
    app.mount("/media", CORSStaticFiles(directory="temp"), name="media")
else:
    app.mount("/media", CORSStaticFiles(directory="temp"), name="media")

# include the routes
app.include_router(users.router, prefix="/users")
app.include_router(pipelines.router, prefix="/video-pipelines")



@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)