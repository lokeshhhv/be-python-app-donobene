

# --- Homebrew/WeasyPrint library path fix for macOS subprocesses ---
import os
os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/lib"
os.environ["PKG_CONFIG_PATH"] = "/opt/homebrew/lib/pkgconfig"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

from dotenv import load_dotenv
load_dotenv()

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
    food,
)

# Import routers
from src.api.auth import router as auth_router
from src.api.email_api import router as email_api_router
from src.api.types import router as types_router
from src.api.clothes_categories import router as clothes_categories
from src.api.education_categories import router as education_categories
from src.api.medical_categories import router as medical_categories
from src.api.sports_categories import router as sports_categories
from src.api.shelter_categories import router as shelter_categories
from src.api.food_categories import router as food_categories
from src.api.admin import router as admin_router
from src.api.donor import router as donor_router


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
app.include_router(email_api_router, prefix="/email", tags=["Email"])
app.include_router(types_router)
app.include_router(clothes_categories)
app.include_router(education_categories)
app.include_router(medical_categories)
app.include_router(sports_categories)
app.include_router(shelter_categories)
app.include_router(food_categories)
app.include_router(admin_router)
app.include_router(donor_router)

# Health check
@app.get("/")
async def health_check():
    return {"status": "ok"}

# Create tables on startup
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)