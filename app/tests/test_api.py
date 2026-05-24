# Verifica que el endpoint de salud responde correctamente y devuelve
# los campos mínimos esperados: status y timestamp.
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


# Verifica que el listado de pagos responde con la estructura correcta:
# una lista de pagos y un contador total, independientemente de si hay datos.
def test_get_payments(client):
    response = client.get("/payments")
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert "total" in data
    assert isinstance(data["payments"], list)


# Verifica el flujo completo de creación de un pago válido:
# código 201, campos obligatorios presentes y valores correctos.
def test_create_payment_valid(client):
    response = client.post("/payments", json={"amount": 99.99, "currency": "EUR"})
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 99.99
    assert data["currency"] == "EUR"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


# Verifica que un importe negativo es rechazado.
# Regla de negocio: ningún pago puede tener importe menor que cero.
def test_create_payment_negative_amount(client):
    response = client.post("/payments", json={"amount": -50, "currency": "EUR"})
    assert response.status_code == 422


# Verifica el caso límite del importe cero.
# El campo está definido como gt=0 (estrictamente mayor que cero),
# por lo que 0 debe ser rechazado igual que cualquier negativo.
def test_create_payment_zero_amount(client):
    response = client.post("/payments", json={"amount": 0, "currency": "EUR"})
    assert response.status_code == 422


# Verifica que una moneda con formato incorrecto es rechazada.
# El patrón exige exactamente 3 letras mayúsculas (ISO 4217: EUR, USD, GBP...).
def test_create_payment_invalid_currency(client):
    response = client.post("/payments", json={"amount": 100, "currency": "eurosss"})
    assert response.status_code == 422


# Verifica que el campo amount es obligatorio.
# Una petición sin él debe ser rechazada con error de validación.
def test_create_payment_missing_amount(client):
    response = client.post("/payments", json={"currency": "EUR"})
    assert response.status_code == 422


# Verifica la consistencia entre creación y listado:
# un pago creado debe incrementar el contador total del listado.
def test_get_payments_after_creation(client):
    initial = client.get("/payments").json()["total"]
    client.post("/payments", json={"amount": 50.0, "currency": "USD"})
    response = client.get("/payments")
    assert response.status_code == 200
    assert response.json()["total"] == initial + 1