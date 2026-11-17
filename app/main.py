from fastapi import FastAPI

from .routes import router

app = FastAPI(title="Keitaro Campaign Manager")
app.include_router(router)
