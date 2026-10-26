from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_swagger import patch_fastapi

import app.db.models
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.db.lifespan import lifespan
from app.domains.auth.auth_routes import router as auth_router
from app.domains.event_format.routes import router as event_format_routes
from app.domains.rooms.buildings_routes import router as buildings_router
from app.domains.rooms.routes import router as rooms_router
from app.domains.users.routes import router as user_router

configure_logging()

app = FastAPI(
    title="Demo app",
    lifespan=lifespan,
)
patch_fastapi(app, docs_url="/api/docs")

register_exception_handlers(app)
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

app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(event_format_routes, prefix="/api")
app.include_router(buildings_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "okey"}


@app.get("/")
def root():
    return {
        "message": "Welcome to fastapi API",
        "docs": "/api/docs",
    }