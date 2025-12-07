from fastapi import FastAPI
from api.routes import users, pipelines

app = FastAPI(title="Vidinie API", description="API for Vidinie", version="0.1.0")

app.include_router(users.router, prefix="/users")
app.include_router(pipelines.router, prefix="/pipelines")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}