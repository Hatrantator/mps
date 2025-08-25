#from fastapi import FastAPI
#from .db import database
#
#app = FastAPI(title="Mydroponic")
#
#@app.on_event("startup")
#async def startup():
#    await database.connect()
#
#@app.on_event("shutdown")
#async def shutdown():
#    await database.disconnect()
#
#@app.get("/")
#async def read_root():
#    return {"message": "Hello from Mydroponic!"}
#
#@app.get("/plants")
#async def get_plants():
#    query = "SELECT * FROM plants;"
#    rows = await database.fetch_all(query)
#    return {"plants": rows}

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey, DECIMAL, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
#from .db import DATABASE_URL
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://myuser:mypassword@mydroponic-db:5432/mydroponic")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# -------------------
# Database Models
# -------------------
class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    floors = relationship("Floor", back_populates="farm", cascade="all, delete")

class Floor(Base):
    __tablename__ = "floors"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    level = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    farm = relationship("Farm", back_populates="floors")
    pots = relationship("Pot", back_populates="floor", cascade="all, delete")

class Pot(Base):
    __tablename__ = "pots"
    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    location_code = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    floor = relationship("Floor", back_populates="pots")
    plants = relationship("Plant", back_populates="pot", cascade="all, delete")

class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    pot_id = Column(Integer, ForeignKey("pots.id", ondelete="SET NULL"))
    qr_code = Column(String, unique=True)
    species = Column(String)
    variety = Column(String)
    germination_date = Column(Date)
    planting_date = Column(Date)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    pot = relationship("Pot", back_populates="plants")
    harvests = relationship("HarvestDate", back_populates="plant", cascade="all, delete")

class HarvestDate(Base):
    __tablename__ = "harvest_dates"
    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    harvest_date = Column(Date, nullable=False)
    yield_weight = Column(DECIMAL(10, 2))
    created_at = Column(TIMESTAMP, server_default=func.now())
    plant = relationship("Plant", back_populates="harvests")

# Create tables
Base.metadata.create_all(bind=engine)

# -------------------
# Pydantic Schemas
# -------------------
class FarmCreate(BaseModel):
    name: str
    location: Optional[str] = None

class FloorCreate(BaseModel):
    farm_id: int
    name: str
    level: Optional[int] = None

class PotCreate(BaseModel):
    floor_id: int
    location_code: str

class PlantCreate(BaseModel):
    pot_id: int
    qr_code: str
    species: str
    variety: Optional[str] = None
    germination_date: Optional[str] = None
    planting_date: Optional[str] = None

class HarvestCreate(BaseModel):
    plant_id: int
    harvest_date: str
    yield_weight: Optional[float] = None

# -------------------
# FastAPI App
# -------------------
app = FastAPI(title="Mydroponic")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- Farms ----
@app.post("/farms")
def create_farm(farm: FarmCreate, db: Session = Depends(get_db)):
    db_farm = Farm(name=farm.name, location=farm.location)
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm

@app.get("/farms")
def list_farms(db: Session = Depends(get_db)):
    return db.query(Farm).all()

# ---- Floors ----
@app.post("/floors")
def create_floor(floor: FloorCreate, db: Session = Depends(get_db)):
    db_floor = Floor(**floor.dict())
    db.add(db_floor)
    db.commit()
    db.refresh(db_floor)
    return db_floor

@app.get("/floors")
def list_floors(db: Session = Depends(get_db)):
    return db.query(Floor).all()

# ---- Pots ----
@app.post("/pots")
def create_pot(pot: PotCreate, db: Session = Depends(get_db)):
    db_pot = Pot(**pot.dict())
    db.add(db_pot)
    db.commit()
    db.refresh(db_pot)
    return db_pot

@app.get("/pots")
def list_pots(db: Session = Depends(get_db)):
    return db.query(Pot).all()

# ---- Plants ----
@app.post("/plants")
def create_plant(plant: PlantCreate, db: Session = Depends(get_db)):
    db_plant = Plant(**plant.dict())
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant

@app.get("/plants")
def list_plants(db: Session = Depends(get_db)):
    return db.query(Plant).all()

# ---- Harvests ----
@app.post("/harvests")
def create_harvest(harvest: HarvestCreate, db: Session = Depends(get_db)):
    db_harvest = HarvestDate(**harvest.dict())
    db.add(db_harvest)
    db.commit()
    db.refresh(db_harvest)
    return db_harvest

@app.get("/harvests")
def list_harvests(db: Session = Depends(get_db)):
    return db.query(HarvestDate).all()