from fastapi import FastAPI
from api.routes import users, pipelines
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="vidinie backend service api", description="API for Vidinie", version="0.1.0", openapi_url="/openapi.json")

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
            if message["type"] == "http.response.start":
                # add cors headers to static file responses
                headers = dict(message.get("headers", []))
                headers[b"access-control-allow-origin"] = b"http://localhost:3000" # remember to update this to the actual frontend url when deploying
                headers[b"access-control-allow-credentials"] = b"true"
                headers[b"access-control-allow-methods"] = b"*"
                headers[b"access-control-allow-headers"] = b"*"
                message["headers"] = list(headers.items())
            await send(message)
        
        await super().__call__(scope, receive, send_wrapper)

app.mount("/media", CORSStaticFiles(directory="temp"), name="media")

app.include_router(users.router, prefix="/users")
app.include_router(pipelines.router, prefix="/video-pipelines")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)