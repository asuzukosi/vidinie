from fastapi import FastAPI
from api.routes import users, pipelines
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Vidinie API", description="API for Vidinie", version="0.1.0", openapi_url="/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(users.router, prefix="/users")
app.include_router(pipelines.router, prefix="/pipelines")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)