from fastapi import FastAPI

from app.api.routes import auth, campaigns, references, streams

app = FastAPI(title="Keitaro Campaign Manager")
for r in (auth.router, references.router, campaigns.router, streams.router):
    app.include_router(r, prefix="/api")
