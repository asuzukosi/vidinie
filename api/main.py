from fastapi import FastAPI, HTTPException
from api.routes import users, pipelines
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from api.core.signals import connect_to_broadcast, disconnect_from_broadcast
from api.core.config import initialize_config, destroy_config
from api.core.db import initialize_db, disconnect_from_db
from core.utils.config_loader import config
from core.utils.logger import get_logger
from core import storage
from fastapi.responses import RedirectResponse, FileResponse
from pathlib import Path

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
                   "https://vidinie.com", "https://app.vidinie.com", "https://api.vidinie.com"] + [os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# where rendered files land on this machine
output_dir = str(config.output_directory)
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)


@app.get("/media/{path:path}", include_in_schema=False)
def media(path: str):
    """serve a file this machine rendered, or redirect to r2 for one it did not."""
    requested = Path(output_dir).joinpath(path).resolve()
    # a mount used to guard this; a plain join would let ../ escape outputs/
    if not requested.is_relative_to(Path(output_dir).resolve()):
        raise HTTPException(status_code=404, detail="not found")

    if requested.is_file():
        return FileResponse(str(requested))

    signed_url = storage.media.url_for(path)
    if not signed_url:
        raise HTTPException(status_code=404, detail="not found")
    return RedirectResponse(signed_url)


# include the routes
app.include_router(users.router, prefix="/users")
app.include_router(pipelines.router, prefix="/video-pipelines")



@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)