from fastapi import FastAPI
from app.api import auth, projects

app = FastAPI(title="DevCanvas API")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])