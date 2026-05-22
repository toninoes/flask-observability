from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='EUR')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

with app.app_context():
    db.create_all()

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route('/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    return jsonify({"payments": [p.to_dict() for p in payments], "total": len(payments)})

@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    payment = Payment(
        amount=data.get('amount'),
        currency=data.get('currency', 'EUR')
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify(payment.to_dict()), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
