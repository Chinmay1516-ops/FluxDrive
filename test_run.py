import os
from dotenv import load_dotenv
from optimizer import find_optimal_speed

load_dotenv() 

MY_ORS_KEY = os.getenv("ORS_KEY")
MY_WEATHER_KEY = os.getenv("WEATHER_KEY")

tata_nexon = {
    "name": "Tata Nexon EV",
    "weight_kg": 1400,
    "battery_capacity_kwh": 40.5,
    "drag_coefficient": 0.35,
    "frontal_area": 2.5,
}

pune_lat, pune_lon = 18.5204, 73.8567
lonavala_lat, lonavala_lon = 18.7481, 73.4072

print("FLUXDRIVE")

optimization_result = find_optimal_speed(
    car_specs=tata_nexon, 
    start_lat=pune_lat, start_lon=pune_lon, 
    end_lat=lonavala_lat, end_lon=lonavala_lon,
    ors_key=MY_ORS_KEY,
    weather_key=MY_WEATHER_KEY
)

print("\nOPTIMIZATION COMPLETE")
if optimization_result["status"] == "success":
    print(f"Vehicle: {tata_nexon['name']}")
    print(f"Route: Pune -> Lonavala")
    print(f"Distance: {optimization_result['total_distance_km']} km")
    print(f"Conditions: {optimization_result['weather_used']}")
    print(f"-----------------------------------")
    print(f"Max Recommended Speed: {optimization_result['recommended_speed_kmh']} km/h")
    print(f"Energy Consumed: {optimization_result['total_energy_kwh']} kWh")
    print(f"Battery on Arrival: {optimization_result['estimated_arrival_battery']}%")
else:
    print(optimization_result["message"])