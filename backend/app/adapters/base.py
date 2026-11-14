from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ExternalProduct:
    external_id: str
    name: str
    description: str
    price: Decimal
    currency: str
    stock_quantity: int


class BoutiqueCatalogueAdapter(Protocol):
    integration_type: str

    def fetch_products(self) -> list[ExternalProduct]:
        """Fetch the current product catalogue from one boutique."""
        ...
