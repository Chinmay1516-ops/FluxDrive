from fastapi import FastAPI, Form
from db import SessionLocal
from models import EVCar
from seed import create_tables, seed_dummy_cars
from geolocation import get_coordinates
from optimizer import find_optimal_speed
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

create_tables()
seed_dummy_cars()

ORS_KEY = os.getenv("ORS_KEY")
WEATHER_KEY = os.getenv("WEATHER_KEY")


@app.get("/")
def home():
    return {"message": "EcoRoute EV backend is running"}


@app.post("/getdata/")
def getdata(
    Source: str = Form(...),
    Destination: str = Form(...),
    Car_Model: str = Form(...),
    Battery_percentage: int = Form(...)
):
    db = SessionLocal()

    try:
        selected_car = db.query(EVCar).filter(EVCar.name == Car_Model).first()

        if selected_car is None:
            return {"status": "failed", "error": "This car is not in database"}

        source_coords = get_coordinates(Source)
        destination_coords = get_coordinates(Destination)

        if source_coords is None:
            return {"status": "failed", "error": "Source location not found"}

        if destination_coords is None:
            return {"status": "failed", "error": "Destination location not found"}

        car_specs = {
            "weight_kg": selected_car.weight_kg,
            "battery_capacity_kwh": selected_car.battery_capacity_kwh,
            "drag_coefficient": selected_car.drag_coefficient,
            "frontal_area": selected_car.frontal_area
        }

        result = find_optimal_speed(
            car_specs=car_specs,
            start_lat=source_coords["lat"],
            start_lon=source_coords["lon"],
            end_lat=destination_coords["lat"],
            end_lon=destination_coords["lon"],
            ors_key=ORS_KEY,
            weather_key=WEATHER_KEY,
            current_battery_percent=Battery_percentage 
        )

        if result.get("status") != "success":
            return result

        return {
            "status": "success",
            "source": Source,
            "destination": Destination,
            "source_coordinates": source_coords,
            "destination_coordinates": destination_coords,
            "car_model": selected_car.name,
            "battery_capacity_kwh": selected_car.battery_capacity_kwh,
            "input_battery_percentage": Battery_percentage,
            "routes": result["routes"]
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()