from fastapi import FastAPI
from api.routes import users, pipelines
app = FastAPI()

app.include_router(users.router, prefix="/users")
app.include_router(pipelines.router, prefix="/pipelines")

@app.get("/health")
def health_check():
    return {"status": "ok"}