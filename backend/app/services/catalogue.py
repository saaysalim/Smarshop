from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..adapters.base import BoutiqueCatalogueAdapter
from ..models import Boutique, Product


def sync_boutique_catalogue(
    db: Session,
    boutique: Boutique,
    adapter: BoutiqueCatalogueAdapter,
) -> tuple[int, int, int]:
    """Synchronise products from one boutique; returns received/created/updated."""
    external_products = adapter.fetch_products()
    created = 0
    updated = 0

    for item in external_products:
        product = db.scalar(
            select(Product).where(
                Product.boutique_id == boutique.id,
                Product.external_id == item.external_id,
            )
        )
        if product is None:
            product = Product(
                boutique_id=boutique.id,
                external_id=item.external_id,
                name=item.name,
                description=item.description,
                price=item.price,
                currency=item.currency,
                stock_quantity=item.stock_quantity,
            )
            db.add(product)
            created += 1
        else:
            product.name = item.name
            product.description = item.description
            product.price = item.price
            product.currency = item.currency
            product.stock_quantity = item.stock_quantity
            updated += 1

    db.commit()
    return len(external_products), created, updated


def get_catalogue(
    db: Session,
    query: str | None = None,
    boutique_id: int | None = None,
    stock_only: bool = False,
):
    statement = select(Product).options(joinedload(Product.boutique)).order_by(Product.id)
    if query:
        statement = statement.where(Product.name.ilike(f"%{query}%"))
    if boutique_id is not None:
        statement = statement.where(Product.boutique_id == boutique_id)
    if stock_only:
        statement = statement.where(Product.stock_quantity > 0)
    return db.scalars(statement).all()
