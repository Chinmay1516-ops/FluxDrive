from db import Base, engine, SessionLocal
from models import EVCar, DUMMY_CARS


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_dummy_cars():
    db = SessionLocal()

    existing_cars = db.query(EVCar).count()

    if existing_cars == 0:
        for car in DUMMY_CARS:
            new_car = EVCar(**car)
            db.add(new_car)

        db.commit()

    db.close()