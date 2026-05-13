from fastapi import FastAPI, Form
from db import SessionLocal
from models import EVCar
from seed import create_tables, seed_dummy_cars
from geolocation import get_coordinates
from engine import calculate_true_range
import os
from dotenv import load_dotenv
from mapping import get_route_data

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

        result = calculate_true_range(
            car_specs=car_specs,
            start_lat=source_coords["lat"],
            start_lon=source_coords["lon"],
            end_lat=destination_coords["lat"],
            end_lon=destination_coords["lon"],
        
            ors_key=ORS_KEY,
            weather_key=WEATHER_KEY
        )
   

        if result.get("status") != "success":
            return result

        battery_left = result["battery_left_percent"]
        route_points = []

        for point in result["3d_path"]:

         route_points.append({
         "lat": point[1],
         "lon": point[0],
         "elevation": point[2]
    })
        if battery_left < 20:
            risk = "high"
            message = "Battery may be low on arrival"
        else:
            risk = "low"
            message = "Good to go"

        return {
            "status": "success",
            "source": Source,
            "destination": Destination,
            "source_coordinates": source_coords,
            "destination_coordinates": destination_coords,
            "car_model": selected_car.name,
            "battery_capacity_kwh": selected_car.battery_capacity_kwh,
            "input_battery_percentage": Battery_percentage,
            "distance_km": result["total_distance_km"],
            "weather_used": result["weather_used"],
            "energy_used_kwh": result["energy_used_kwh"],
            "battery_left_percent": result["battery_left_percent"],
            "risk_level": risk,
            "message": message,
            "route_points": route_points,
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()