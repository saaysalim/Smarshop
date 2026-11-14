from decimal import Decimal

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Boutique, Product

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def isolate_database():
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)

    with TestingSessionLocal() as db:
        boutique_a = Boutique(name="Boutique A")
        boutique_b = Boutique(name="Boutique B")
        db.add_all([boutique_a, boutique_b])
        db.flush()

        products = [
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
        for index, (name, description, price, stock, boutique) in enumerate(products):
            external_id = (
                f"A-{1001 + index}"
                if boutique is boutique_a
                else f"B-{2001 + index - 5}"
            )
            db.add(
                Product(
                    external_id=external_id,
                    name=name,
                    description=description,
                    price=Decimal(price),
                    stock_quantity=0 if index == 0 else stock,
                    boutique=boutique,
                )
            )
        db.commit()

    yield

    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


@pytest.fixture
def clear_boutique_a_products():
    with TestingSessionLocal() as db:
        db.execute(delete(Product).where(Product.boutique_id == 1))
        db.commit()
