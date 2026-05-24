def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_get_payments(client):
    response = client.get("/payments")
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert "total" in data
    assert isinstance(data["payments"], list)


def test_create_payment_valid(client):
    response = client.post("/payments", json={"amount": 99.99, "currency": "EUR"})
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 99.99
    assert data["currency"] == "EUR"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


def test_create_payment_negative_amount(client):
    response = client.post("/payments", json={"amount": -50, "currency": "EUR"})
    assert response.status_code == 422


def test_create_payment_invalid_currency(client):
    response = client.post("/payments", json={"amount": 100, "currency": "eurosss"})
    assert response.status_code == 422


def test_create_payment_missing_amount(client):
    response = client.post("/payments", json={"currency": "EUR"})
    assert response.status_code == 422


def test_get_payments_after_creation(client):
    client.post("/payments", json={"amount": 50.0, "currency": "USD"})
    response = client.get("/payments")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    