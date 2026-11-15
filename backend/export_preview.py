import json
from pathlib import Path

from app.adapters.demo import DemoBoutiqueAAdapter, DemoBoutiqueBAdapter


def main():
    boutiques = []
    products = []
    for boutique_id, adapter in (
        (1, DemoBoutiqueAAdapter()),
        (2, DemoBoutiqueBAdapter()),
    ):
        name = f"Boutique {'A' if boutique_id == 1 else 'B'}"
        boutiques.append(
            {"id": boutique_id, "name": name, "integration_type": "demo"}
        )
        for item in adapter.fetch_products():
            products.append(
                {
                    "id": len(products) + 1,
                    "boutique_id": boutique_id,
                    "boutique": name,
                    "name": item.name,
                    "description": item.description,
                    "price": float(item.price),
                    "currency": item.currency,
                    "stock_quantity": item.stock_quantity,
                }
            )

    output = Path(__file__).resolve().parent.parent / "frontend" / "public" / "demo-catalogue.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"boutiques": boutiques, "products": products}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {len(products)} sample products to {output}")


if __name__ == "__main__":
    main()
