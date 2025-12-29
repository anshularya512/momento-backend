from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Integer, String, Float
from db import Base

# --- Database Models ---

class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True) # Changed to String
    merchant = Column(String)
    amount = Column(Float)
    interval_days = Column(Integer)
    type = Column(String)             
    confidence = Column(Float)

class IncomeSource(Base):
    __tablename__ = "income_sources"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True) # Changed to String
    amount = Column(Float)
    interval_days = Column(Integer)
    confidence = Column(Float)

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    token = Column(String, unique=True)

# --- Pydantic Schemas (API Validation) ---

class StatementUpload(BaseModel):
    user_id: str  # Changed from int to str
    text: str

class BulkTransaction(BaseModel):
    user_id: str  # Changed from int to str
    amount: float
    type: str 
    timestamp: int
    raw: Optional[str] = None