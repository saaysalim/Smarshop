from decimal import Decimal
from .base import ExternalProduct


class DemoBoutiqueAAdapter:
    """Simulates Boutique A's external catalogue API."""

    integration_type = "demo"

    def fetch_products(self) -> list[ExternalProduct]:
        return [
            ExternalProduct("A-1001", "Leather Tote Bag", "Classic everyday leather tote.", Decimal("120.00"), "EUR", 8),
            ExternalProduct("A-1002", "Wool Scarf", "Soft wool scarf.", Decimal("65.00"), "EUR", 12),
            ExternalProduct("A-1003", "Travel Wallet", "Compact travel wallet.", Decimal("48.00"), "EUR", 15),
            ExternalProduct("A-1004", "Classic Sunglasses", "Timeless frame with UV protection.", Decimal("95.00"), "EUR", 6),
            ExternalProduct("A-1005", "Cotton Shirt", "Regular-fit cotton shirt.", Decimal("75.00"), "EUR", 10),
        ]


class DemoBoutiqueBAdapter:
    """Simulates Boutique B's external catalogue API."""

    integration_type = "demo"

    def fetch_products(self) -> list[ExternalProduct]:
        return [
            ExternalProduct("B-2001", "Running Shoes", "Lightweight everyday trainers.", Decimal("110.00"), "EUR", 9),
            ExternalProduct("B-2002", "Ceramic Watch", "Minimal design wristwatch.", Decimal("180.00"), "EUR", 4),
            ExternalProduct("B-2003", "Crossbody Bag", "Small crossbody bag.", Decimal("135.00"), "EUR", 7),
            ExternalProduct("B-2004", "Knit Jumper", "Comfortable knit jumper.", Decimal("145.00"), "EUR", 5),
            ExternalProduct("B-2005", "Travel Backpack", "Practical cabin-size backpack.", Decimal("89.00"), "EUR", 11),
        ]
