import os
import json
import requests
import redis
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session


CURRENCY_API_URL = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies"
)
CACHE_TTL = 60 * 30
DATABASE_URL = os.getenv("DB_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


redis_client = redis.from_url(REDIS_URL, decode_responses=True)


Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS rate;"))
    conn.execute(text("SET search_path TO rate;"))


class ConversionLog(Base):
    __tablename__ = "conversion_logs"
    __table_args__ = {"schema": "rate"}

    id = Column(Integer, primary_key=True, index=True)
    base_currency = Column(String, nullable=False)
    target_currency = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    converted_amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        db.execute(text("SET search_path TO rate;"))
        yield db
    finally:
        db.close()


app = FastAPI()


class ConversionRequest(BaseModel):
    amount: float
    base_currency: str
    target_currency: str


def fetch_rates(base_currency: str):
    """Fetch exchange rates JSON from CDN or Redis cache"""
    base_currency = base_currency.lower()
    cache_key = f"rates:{base_currency}"

    if cached := redis_client.get(cache_key):
        return json.loads(cached)

    url = f"{CURRENCY_API_URL}/{base_currency}.json"
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch exchange rates")

    data = response.json()
    rates = data[base_currency]

    redis_client.setex(cache_key, CACHE_TTL, json.dumps(rates))
    return rates


@app.post("/convert")
def convert(req: ConversionRequest, db: Session = Depends(get_db)):
    base = req.base_currency.lower()
    target = req.target_currency.lower()

    rates = fetch_rates(base)

    if target not in rates:
        raise HTTPException(status_code=400, detail="Invalid target currency")

    rate = rates[target]
    converted_amount = req.amount * rate

    log = ConversionLog(
        base_currency=base.upper(),
        target_currency=target.upper(),
        amount=req.amount,
        converted_amount=converted_amount,
    )
    db.add(log)
    db.commit()

    return {
        "base_currency": base.upper(),
        "target_currency": target.upper(),
        "amount": req.amount,
        "converted_amount": converted_amount,
        "rate": rate,
    }
