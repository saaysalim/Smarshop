from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_database_connection():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_products_endpoint_returns_catalogue():
    with TestClient(app) as client:
        response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 10
    assert {p["boutique"] for p in products} == {"Boutique A", "Boutique B"}
    assert all(p["currency"] == "EUR" for p in products)


def test_products_endpoint_can_filter_out_of_stock_items():
    with TestClient(app) as client:
        response = client.get("/api/products", params={"stock_only": True})

    assert response.status_code == 200
    assert len(response.json()) == 9
    assert all(product["stock_quantity"] > 0 for product in response.json())


def test_boutiques_endpoint_includes_configured_integration_type():
    with TestClient(app) as client:
        response = client.get("/api/boutiques")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Boutique A", "integration_type": "demo"},
        {"id": 2, "name": "Boutique B", "integration_type": "demo"},
    ]


def test_checkout_creates_order_and_decreases_stock():
    with TestClient(app) as client:
        before = next(
            product
            for product in client.get(
                "/api/products", params={"boutique_id": 1}
            ).json()
            if product["stock_quantity"] > 0
        )
        response = client.post(
            "/api/orders",
            json={"items": [{"product_id": before["id"], "quantity": 2}]},
        )
        after = next(
            product
            for product in client.get(
                "/api/products", params={"boutique_id": 1}
            ).json()
            if product["id"] == before["id"]
        )

    assert response.status_code == 201
    order = response.json()
    assert order["total_amount"] == before["price"] * 2
    assert order["currency"] == "EUR"
    assert order["items"] == [
        {
            "product_id": before["id"],
            "product_name": before["name"],
            "unit_price": before["price"],
            "quantity": 2,
        }
    ]
    assert after["stock_quantity"] == before["stock_quantity"] - 2


def test_checkout_rejects_insufficient_stock_without_decreasing_stock():
    with TestClient(app) as client:
        product = next(
            product
            for product in client.get("/api/products").json()
            if product["stock_quantity"] > 0
        )
        product_id = product["id"]
        response = client.post(
            "/api/orders",
            json={"items": [{"product_id": product_id, "quantity": 99}]},
        )
        after = next(
            item
            for item in client.get("/api/products").json()
            if item["id"] == product_id
        )

    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["detail"]
    assert after["stock_quantity"] == product["stock_quantity"]
