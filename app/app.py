from flask import Flask, jsonify, request
from datetime import datetime, timezone
import uuid

app = Flask(__name__)

payments = []

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route('/payments', methods=['GET'])
def get_payments():
    return jsonify({"payments": payments, "total": len(payments)})

@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    payment = {
        "id": str(uuid.uuid4()),
        "amount": data.get("amount"),
        "currency": data.get("currency", "EUR"),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    payments.append(payment)
    return jsonify(payment), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
