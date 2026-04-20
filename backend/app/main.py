from fastapi import FastAPI
from app.api.health import router

app = FastAPI(title="Sentineloops API")

app.include_router(router)
