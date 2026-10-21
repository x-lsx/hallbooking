from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.lifespan import lifespan

configure_logging()

app = FastAPI(
    title="Demo app",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "okey"}


@app.get("/")
def root():
    return {
        "message": "Welcome to fastapi API",
        "docs": "/api/docs",
    }