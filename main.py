from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from tronpy import Tron
from tronpy.providers import HTTPProvider

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()
client = Tron(HTTPProvider("https://api.trongrid.io"))


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True)
    balance = Column(Integer)
    bandwidth = Column(Integer)
    energy = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/address-info/")
def get_address_info(address: str, db: Session = Depends(get_db)):
    try:
        account = client.get_account(address)
        balance = account.get("balance", 0)
        bandwidth = client.get_account_resource(address).get("freeNetUsed", 0)
        energy = client.get_account_resource(address).get("EnergyLimit", 0)

        new_request = RequestLog(address=address, balance=balance, bandwidth=bandwidth, energy=energy)
        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        return {"address": address, "balance": balance, "bandwidth": bandwidth, "energy": energy}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/requests/")
def get_requests(
        db: Session = Depends(get_db),
        skip: int = Query(0, alias="offset"),
        limit: int = Query(10, alias="limit")
):
    requests = db.query(RequestLog).order_by(RequestLog.timestamp.desc()).offset(skip).limit(limit).all()
    return {"requests": requests}
