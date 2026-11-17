from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, campaigns, references, streams
from app.services.connection import load_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_connection()
    yield


app = FastAPI(title="Keitaro Campaign Manager", lifespan=lifespan)
for r in (auth.router, references.router, campaigns.router, streams.router):
    app.include_router(r, prefix="/api")
