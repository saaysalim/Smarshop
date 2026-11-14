from fastapi.testclient import TestClient

from app.main import app

def test_products_can_be_filtered_by_boutique_and_search():
    with TestClient(app) as client:
        all_products = client.get("/api/products")
        boutique_a = client.get("/api/products", params={"boutique_id": 1})
        searched = client.get("/api/products", params={"q": "watch"})

    assert all_products.status_code == 200
    assert len(all_products.json()) == 10
    assert len(boutique_a.json()) == 5
    assert all(p["boutique"] == "Boutique A" for p in boutique_a.json())
    assert len(searched.json()) == 1
    assert searched.json()[0]["name"] == "Ceramic Watch"


def test_catalogue_sync_is_repeatable_without_duplicate_products(
    clear_boutique_a_products,
):
    with TestClient(app) as client:
        first = client.post("/api/admin/boutiques/1/catalogue-sync")
        second = client.post("/api/admin/boutiques/1/catalogue-sync")
        products = client.get("/api/products", params={"boutique_id": 1})

    assert first.status_code == 200
    assert first.json()["received"] == 5
    assert first.json()["created"] == 5
    assert second.status_code == 200
    assert second.json()["created"] == 0
    assert second.json()["updated"] == 5
    assert len(products.json()) == 5
