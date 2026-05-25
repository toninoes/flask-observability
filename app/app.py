from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, Column, String, Numeric, DateTime
from sqlalchemy.orm import DeclarativeBase, Session

import uuid
import os
import structlog
import logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+psycopg://"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    status = Column(String(20), default="pending")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Importe mayor que cero")
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount: float
    currency: str
    status: str
    created_at: datetime


class PaymentsListResponse(BaseModel):
    payments: list[PaymentResponse]
    total: int

# ---------------------------------------------------------------------------
# Custom metrics
# ---------------------------------------------------------------------------
payments_created_total = Counter(
    "payments_created_total",
    "Total de pagos creados exitosamente",
    ["currency"],
)

payments_amount_euros = Histogram(
    "payments_amount_euros",
    "Distribución de importes de pago",
    ["currency"],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000],
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Payment API", version="1.0.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/payments", response_model=PaymentsListResponse)
def get_payments():
    with Session(engine) as session:
        payments = session.query(Payment).all()
        return {
            "payments": [PaymentResponse.model_validate(p) for p in payments],
            "total": len(payments),
        }


@app.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(payment: PaymentRequest):
    with Session(engine) as session:
        new_payment = Payment(
            amount=payment.amount,
            currency=payment.currency,
        )
        session.add(new_payment)
        session.commit()
        session.refresh(new_payment)
        payments_created_total.labels(currency=payment.currency).inc()
        payments_amount_euros.labels(currency=payment.currency).observe(float(new_payment.amount))
        logger.info(
            "payment_created",
            payment_id=new_payment.id,
            amount=float(new_payment.amount),
            currency=new_payment.currency,
        )
        return PaymentResponse.model_validate(new_payment)
 