# models_extra.py
from sqlalchemy import Column, Integer, String, Float
from db import Base

class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    merchant = Column(String)
    amount = Column(Float)
    interval_days = Column(Integer)   # usually 30
    type = Column(String)             # debit / credit
    confidence = Column(Float)         # 0–1


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    interval_days = Column(Integer)
    confidence = Column(Float)


from sqlalchemy import Column, Integer, String

class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    token = Column(String, unique=True)


from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BulkTransaction(BaseModel):
    user_id: int
    timestamp: datetime
    amount: float
    type: str  # "debit" | "credit"
    source: Optional[str] = "statement"
    raw: Optional[str] = None


class StatementUpload(BaseModel):
    user_id: int
    text: str
