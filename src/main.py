from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.base import Base
from src.db.session import engine

# Import model modules so SQLAlchemy metadata includes all tables.
from src.models import (
    clothes,
    education,
    medical,
    shelter,
    sports,
    types,
)

# Import routers
from src.api.auth import router as auth_router
from src.api.email_auth import router as email_auth_router
from src.api.types import router as types_router
from src.api.clothes_categories import router as clothes_categories
from src.api.education_categories import router as education_categories
from src.api.medical_categories import router as medical_categories
from src.api.sports_categories import router as sports_categories
from src.api.shelter_categories import router as shelter_categories

app = FastAPI(title="DonoBene API", version="1.0.0")

# CORS (allow all for now - dev only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(email_auth_router)
app.include_router(types_router)
app.include_router(clothes_categories)
app.include_router(education_categories)
app.include_router(medical_categories)
app.include_router(sports_categories)
app.include_router(shelter_categories)

# Health check
@app.get("/")
async def health_check():
    return {"status": "ok"}

# Create tables on startup
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)