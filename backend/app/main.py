import os
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Boutique, Product
from .api.catalogue import router as catalogue_router
from .api.orders import router as orders_router


def seed_catalogue():
    with SessionLocal() as db:
        if db.scalar(select(Boutique.id).limit(1)) is not None:
            return

        boutique_a = Boutique(name="Boutique A")
        boutique_b = Boutique(name="Boutique B")
        db.add_all([boutique_a, boutique_b])
        db.flush()

        samples = [
            ("Leather Tote Bag", "Classic everyday leather tote.", "120.00", 8, boutique_a),
            ("Wool Scarf", "Soft wool scarf.", "65.00", 12, boutique_a),
            ("Travel Wallet", "Compact travel wallet.", "48.00", 15, boutique_a),
            ("Classic Sunglasses", "Timeless frame with UV protection.", "95.00", 6, boutique_a),
            ("Cotton Shirt", "Regular-fit cotton shirt.", "75.00", 10, boutique_a),
            ("Running Shoes", "Lightweight everyday trainers.", "110.00", 9, boutique_b),
            ("Ceramic Watch", "Minimal design wristwatch.", "180.00", 4, boutique_b),
            ("Crossbody Bag", "Small crossbody bag.", "135.00", 7, boutique_b),
            ("Knit Jumper", "Comfortable knit jumper.", "145.00", 5, boutique_b),
            ("Travel Backpack", "Practical cabin-size backpack.", "89.00", 11, boutique_b),
        ]
        for index, (name, description, price, stock, boutique) in enumerate(samples):
            prefix = "A" if boutique.name == "Boutique A" else "B"
            external_number = index + 1 if prefix == "A" else index - 4
            db.add(Product(
                external_id=f"{prefix}-{1000 + external_number}" if prefix == "A" else f"{prefix}-{2000 + external_number}",
                name=name,
                description=description,
                price=Decimal(price),
                stock_quantity=stock,
                boutique=boutique,
            ))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_catalogue()
    yield


app = FastAPI(
    title="SmartShop API",
    version="0.1.0",
    description="Starter API for a multi-boutique shopping platform.",
    lifespan=lifespan,
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


app.include_router(catalogue_router)
app.include_router(orders_router)
