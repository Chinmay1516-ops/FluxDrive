from sqlalchemy import Column, Integer, String, Float
from db import Base


class EVCar(Base):
    __tablename__ = "ev_cars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    battery_capacity_kwh = Column(Float, nullable=False)
    drag_coefficient = Column(Float, nullable=False)
    frontal_area = Column(Float, nullable=False)


DUMMY_CARS = [
    {
        "name": "Tesla Model 3",
        "weight_kg": 1840,
        "battery_capacity_kwh": 75,
        "drag_coefficient": 0.23,
        "frontal_area": 2.22,
    },
    {
        "name": "Tata Nexon EV",
        "weight_kg": 1400,
        "battery_capacity_kwh": 40.5,
        "drag_coefficient": 0.35,
        "frontal_area": 2.5,
    },
    {
        "name": "BYD Atto 3",
        "weight_kg": 1680,
        "battery_capacity_kwh": 60.5,
        "drag_coefficient": 0.29,
        "frontal_area": 2.4,
    },
]