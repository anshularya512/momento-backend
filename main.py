# main.py
from fastapi import FastAPI
from db import engine
from models import Base

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "backend live"}
