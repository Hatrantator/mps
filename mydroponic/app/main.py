from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, text, Boolean, Date, ForeignKey, DECIMAL, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
import os
from datetime import datetime, date
import paho.mqtt.client as mqtt
import json

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://myuser:mypassword@mydroponic-db:5432/mydroponic")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# MQTT setup
MQTT_BROKER = "192.168.7.216"
MQTT_PORT = 1883
MQTT_USER = "tx_mqtt"
MQTT_PASSWORD = "mqttpassword"
DISCOVERY_PREFIX = "homeassistant"

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

mqtt_version = "v0.1-alpha"

# -------------------
# Database Models
# -------------------
class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    #floors = relationship("Floor", back_populates="farm", cascade="all, delete")

class Floor(Base):
    __tablename__ = "floors"
    id = Column(Integer, primary_key=True, index=True)
    #farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    level = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    #farm = relationship("Farm", back_populates="floors")
    #pots = relationship("Pot", back_populates="floor", cascade="all, delete")

class Pot(Base):
    __tablename__ = "pots"
    id = Column(Integer, primary_key=True, index=True)
    #floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    location_code = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    #floor = relationship("Floor", back_populates="pots")
    #plants = relationship("Plant", back_populates="pot", cascade="all, delete")

class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    #pot_id = Column(Integer, ForeignKey("pots.id", ondelete="SET NULL"))
    qr_code = Column(String, unique=True)
    species = Column(String)
    variety = Column(String)
    germination_date = Column(Date)
    planting_date = Column(Date)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    #pot = relationship("Pot", back_populates="plants")
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
    #farm_id: int
    name: str
    level: Optional[int] = None

class PotCreate(BaseModel):
    #floor_id: int
    location_code: str

class PlantCreate(BaseModel):
    #pot_id: int
    qr_code: str
    species: str
    variety: Optional[str] = None
    germination_date: Optional[str] = None
    planting_date: Optional[str] = None

class PlantOut(BaseModel):
    id: int
    #pot_id: Optional[int]
    qr_code: str
    species: Optional[str]
    variety: Optional[str]
    germination_date: Optional[str]
    planting_date: Optional[str]
    active: Optional[bool]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class HarvestCreate(BaseModel):
    plant_id: int
    harvest_date: str
    yield_weight: Optional[float] = None

# -------------------
# MQTT App
# -------------------

# ---- Farms ----
def farm_uid(farm) -> str:
    return f"{farm.id}"

def publish_discovery_for_farm(farm):
    uid = farm_uid(farm)
    device = {
        "identifiers": [f"farm_{uid}"],
        "name": f"farm_{farm.name}",
        "manufacturer": "Mydroponics",
        "model": "Modular Hydroponic Tower ",
        "sw_version": mqtt_version
    }
    # Status sensor
    status_cfg_topic = f"{DISCOVERY_PREFIX}/sensor/farm_{uid}_status/config"
    status_cfg_payload = {
        "name": f"Status",
        "unique_id": f"farm_{uid}_status",
        "state_topic": f"farms/{uid}/state",
        "value_template": "{{ value_json.status }}",
        "json_attributes_topic": f"farms/{uid}/state",
        "json_attributes_template": "{{ value_json | tojson }}",
        "icon": "mdi:tractor-variant",
        "device": device
    }
    mqtt_client.publish(status_cfg_topic, json.dumps(status_cfg_payload), retain=True)

def publish_state_for_farm(farm):
    uid = farm_uid(farm)
    topic = f"farms/{uid}/state"
    payload = {
        "id": f"{uid}",
        "name": farm.name,
        "location": farm.location,
        "created_at": str(farm.created_at) if farm.created_at else None
    }
    mqtt_client.publish(topic, json.dumps(payload), retain=True)

def delete_farm_from_ha(uid: str):
    # Publish empty retained payloads to remove entities & state
    topics = [
        f"{DISCOVERY_PREFIX}/sensor/farm_{uid}_status/config",
        f"farms/{uid}/state"
    ]
    for t in topics:
        mqtt_client.publish(t, b"", retain=True)

# ---- Plants ----
def plant_uid(plant) -> str:
    #if plant.qr_code:
        # sanitize qr_code to alnum/underscore just in case
    #    return "qr_" + "".join(ch if ch.isalnum() else "_" for ch in plant.qr_code)
    return f"id{plant.id}"

def publish_discovery_for_plant(plant):
    uid = plant_uid(plant)
    device = {
        "identifiers": [f"plant_{uid}"],
        "name": f"plant_{plant.species}_{plant.variety or 'unknown'}",
        "manufacturer": "Mydroponics",
        "model": "Plant", 
        "sw_version": "1.0"
    }

    # Species sensor
    species_cfg_topic = f"{DISCOVERY_PREFIX}/sensor/plant_{uid}_species/config"
    species_cfg_payload = {
        "name": "Species",
        "unique_id": f"plant_{uid}_species",
        "state_topic": f"plants/{uid}/state",
        "value_template": "{{ value_json.species }}",
        "json_attributes_topic": f"plants/{uid}/state",
        "json_attributes_template": "{{ value_json | tojson }}",
        "icon": "mdi:sprout",
        "device": device
    }
    mqtt_client.publish(species_cfg_topic, json.dumps(species_cfg_payload), retain=True)

    # Variety sensor
    #variety_cfg_topic = f"{DISCOVERY_PREFIX}/sensor/plant_{uid}_variety/config"
    #variety_cfg_payload = {
    #    "name": f"Variety",
    #    "unique_id": f"plant_{uid}_variety",
    #    "state_topic": f"plants/{uid}/state",
    #    "value_template": "{{ value_json.variety }}",
    #    "icon": "mdi:flower-outline",
    #    "device": device
    #}
    #mqtt_client.publish(variety_cfg_topic, json.dumps(variety_cfg_payload), retain=True)

    # Active binary_sensor
    active_cfg_topic = f"{DISCOVERY_PREFIX}/binary_sensor/plant_{uid}_active/config"
    active_cfg_payload = {
        "name": f"Plant Active",
        "unique_id": f"plant_{uid}_active",
        "state_topic": f"plants/{uid}/state",
        "value_template": "{{ 'ON' if value_json.active else 'OFF' }}",
        "payload_on": "ON",
        "payload_off": "OFF",
        "icon": "mdi:power",
        "device": device
    }
    mqtt_client.publish(active_cfg_topic, json.dumps(active_cfg_payload), retain=True)

    # QR sensor
    qr_cfg_topic = f"{DISCOVERY_PREFIX}/sensor/plant_{uid}_qr/config"
    qr_cfg_payload = {
        "name": f"Plant QR Code",
        "unique_id": f"plant_{uid}_active",
        "state_topic": f"plants/{uid}/state",
        "value_template": "{{ value_json.qr_code | default('N/A') }}",
        "icon": "mdi:qrcode",
        "device": device
    }
    mqtt_client.publish(qr_cfg_topic, json.dumps(qr_cfg_payload), retain=True)

def publish_state_for_plant(plant):
    uid = plant_uid(plant)
    topic = f"plants/{uid}/state"
    payload = {
        "id": plant.id,
        #"pot_id": plant.pot_id,
        "qr_code": plant.qr_code,
        "species": plant.species,
        "variety": plant.variety,
        "germination_date": str(plant.germination_date) if plant.germination_date else None,
        "planting_date": str(plant.planting_date) if plant.planting_date else None,
        "active": bool(plant.active) if plant.active is not None else None,
        "created_at": str(plant.created_at) if plant.created_at else None
    }
    mqtt_client.publish(topic, json.dumps(payload), retain=True)

def delete_plant_from_ha(uid: str):
    # Publish empty retained payloads to remove entities & state
    topics = [
        f"{DISCOVERY_PREFIX}/sensor/plant_{uid}_species/config",
        f"{DISCOVERY_PREFIX}/sensor/plant_{uid}_variety/config",
        f"{DISCOVERY_PREFIX}/binary_sensor/plant_{uid}_active/config",
        f"{DISCOVERY_PREFIX}/binary_sensor/plant_{uid}_qr/config",
        f"plants/{uid}/state"
    ]
    for t in topics:
        mqtt_client.publish(t, b"", retain=True)

# ---- Server ----
def publish_discovery_for_server():
    uid = "server01"
    device = {
        "identifiers": [f"{uid}"],
        "name": f"Mydroponic Server",
        "manufacturer": "Mydroponics",
        "model": "Server", 
        "sw_version": "1.0"
    }
    server_cfg_topic = f"{DISCOVERY_PREFIX}/sensor/{uid}_status/config"
    server_cfg_payload = {
        "name": f"Server Status",
        "unique_id": f"{uid}_status",
        "state_topic": f"{uid}_status/state",
        "value_template": "ON",
        "device": device
    }
    mqtt_client.publish(server_cfg_topic, json.dumps(server_cfg_payload), retain=True)

def publish_state_for_server():
    uid = "server01"
    topic = f"{uid}_status/state"
    payload = {
        "id": uid,
        "active": True
    }
    mqtt_client.publish(topic, json.dumps(payload), retain=True)

# -------------------
# FastAPI App
# -------------------
app = FastAPI(title="Mydroponic", root_path="/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    # On boot, (re)announce all plants so HA is always in sync
    db = next(get_db())
    try:
        for plant in db.query(Plant).all():
            publish_discovery_for_plant(plant)
            publish_state_for_plant(plant)
        for farm in db.query(Farm).all():
            publish_discovery_for_farm(farm)
            publish_state_for_farm(farm)
    finally:
        db.close()
    
    publish_discovery_for_server()
    publish_state_for_server()


# ---- Health Check ----
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    status = {"db": "ok"}
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        status["db"] = f"error: {e}"

    # Check each table
    checks = {
        "farms": Farm,
        "floors": Floor,
        "pots": Pot,
        "plants": Plant,
        "harvests": HarvestDate,
    }
    for name, model in checks.items():
        try:
            db.query(model).limit(1).all()
            status[name] = "ok"
        except Exception as e:
            status[name] = f"error: {e}"

    return status

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
    farms = db.query(Farm).all()

    # MQTT publish for each plant
    for farm in farms:
       publish_discovery_for_farm(farm)
       publish_state_for_farm(farm)
    return farms

@app.put("/farms/{farm_id}")
def update_farm(farm_id: int, farm: FarmCreate = Body(...), db: Session = Depends(get_db)):
    db_farm = db.query(Farm).get(farm_id)
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db_farm.name = farm.name
    db_farm.location = farm.location
    db.commit()
    db.refresh(db_farm)
    return db_farm

@app.delete("/farms/{farm_id}")
def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    db_farm = db.query(Farm).get(farm_id)
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db.delete(db_farm)
    db.commit()
    return {"detail": "Farm deleted"}

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

@app.put("/floors/{floor_id}")
def update_floor(floor_id: int, floor: FloorCreate = Body(...), db: Session = Depends(get_db)):
    db_floor = db.query(Floor).get(floor_id)
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    #db_floor.farm_id = floor.farm_id
    db_floor.name = floor.name
    db_floor.level = floor.level
    db.commit()
    db.refresh(db_floor)
    return db_floor

@app.delete("/floors/{floor_id}")
def delete_floor(floor_id: int, db: Session = Depends(get_db)):
    db_floor = db.query(Floor).get(floor_id)
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    db.delete(db_floor)
    db.commit()
    return {"detail": "Floor deleted"}

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

@app.put("/pots/{pot_id}")
def update_pot(pot_id: int, pot: PotCreate = Body(...), db: Session = Depends(get_db)):
    db_pot = db.query(Pot).get(pot_id)
    if not db_pot:
        raise HTTPException(status_code=404, detail="Pot not found")
    #db_pot.floor_id = pot.floor_id
    db_pot.location_code = pot.location_code
    db.commit()
    db.refresh(db_pot)
    return db_pot

@app.delete("/pots/{pot_id}")
def delete_pot(pot_id: int, db: Session = Depends(get_db)):
    db_pot = db.query(Pot).get(pot_id)
    if not db_pot:
        raise HTTPException(status_code=404, detail="Pot not found")
    db.delete(db_pot)
    db.commit()
    return {"detail": "Pot deleted"}

# ---- Plants ----
@app.post("/plants")
def create_plant(plant: PlantCreate, db: Session = Depends(get_db)):
    db_plant = Plant(**plant.dict())
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    publish_discovery_for_plant(db_plant)
    publish_state_for_plant(db_plant)
    return db_plant

@app.get("/plants", response_model=List[PlantOut])
def list_plants(db: Session = Depends(get_db)):
    plants = db.query(Plant).all()

    # MQTT publish for each plant
    for plant in plants:
       publish_discovery_for_plant(plant)
       publish_state_for_plant(plant)
    return plants

@app.put("/plants/{plant_id}")
def update_plant(plant_id: int, plant: PlantCreate = Body(...), db: Session = Depends(get_db)):
    db_plant = db.query(Plant).get(plant_id)
    if not db_plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    #db_plant.pot_id = plant.pot_id
    db_plant.qr_code = plant.qr_code
    db_plant.species = plant.species
    db_plant.variety = plant.variety
    db_plant.germination_date = plant.germination_date
    db_plant.planting_date = plant.planting_date
    db.commit()
    db.refresh(db_plant)
    return db_plant

@app.delete("/plants/{plant_id}")
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    db_plant = db.query(Plant).get(plant_id)
    if not db_plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    db.delete(db_plant)
    db.commit()
    return {"detail": "Plant deleted"}

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

@app.put("/harvests/{harvest_id}")
def update_harvest(harvest_id: int, harvest: HarvestCreate = Body(...), db: Session = Depends(get_db)):
    db_harvest = db.query(HarvestDate).get(harvest_id)
    if not db_harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    db_harvest.plant_id = harvest.plant_id
    db_harvest.harvest_date = harvest.harvest_date
    db_harvest.yield_weight = harvest.yield_weight
    db.commit()
    db.refresh(db_harvest)
    return db_harvest

@app.delete("/harvests/{harvest_id}")
def delete_harvest(harvest_id: int, db: Session = Depends(get_db)):
    db_harvest = db.query(HarvestDate).get(harvest_id)
    if not db_harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    db.delete(db_harvest)
    db.commit()
    return {"detail": "Harvest deleted"}