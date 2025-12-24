# models.py
from sqlalchemy import Column, Integer, String, Float, BigInteger
from db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    type = Column(String)   # credit / debit
    raw = Column(String)
    timestamp = Column(BigInteger)
