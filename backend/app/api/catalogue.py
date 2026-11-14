from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..adapters.registry import get_adapter
from ..database import get_db
from ..models import Boutique
from ..schemas import BoutiqueRead, ProductRead, SyncResult
from ..services.catalogue import get_catalogue, sync_boutique_catalogue

router = APIRouter(prefix="/api", tags=["catalogue"])


@router.get("/boutiques", response_model=list[BoutiqueRead])
def list_boutiques(db: Session = Depends(get_db)):
    boutiques = db.scalars(select(Boutique).order_by(Boutique.id)).all()
    return [
        {
            "id": boutique.id,
            "name": boutique.name,
            "integration_type": (
                adapter.integration_type if adapter else "unconfigured"
            ),
        }
        for boutique in boutiques
        for adapter in [get_adapter(boutique.id)]
    ]


@router.get("/products", response_model=list[ProductRead])
def list_products(
    q: str | None = Query(default=None, description="Search product names"),
    boutique_id: int | None = None,
    stock_only: bool = False,
    db: Session = Depends(get_db),
):
    products = get_catalogue(db, q, boutique_id, stock_only)
    return [
        {
            "id": p.id,
            "boutique_id": p.boutique_id,
            "boutique": p.boutique.name,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "currency": p.currency,
            "stock_quantity": p.stock_quantity,
        }
        for p in products
    ]


@router.post("/admin/boutiques/{boutique_id}/catalogue-sync", response_model=SyncResult)
def sync_catalogue(boutique_id: int, db: Session = Depends(get_db)):
    boutique = db.get(Boutique, boutique_id)
    if boutique is None:
        raise HTTPException(status_code=404, detail="Boutique not found")

    adapter = get_adapter(boutique_id)
    if adapter is None:
        raise HTTPException(
            status_code=501,
            detail="No catalogue adapter is configured for this boutique",
        )

    received, created, updated = sync_boutique_catalogue(db, boutique, adapter)
    return SyncResult(
        boutique_id=boutique.id,
        boutique=boutique.name,
        received=received,
        created=created,
        updated=updated,
        message="Catalogue synchronised successfully",
    )
