from engine import calculate_true_range
from mapping import get_route_data
from weather import get_weather_data

def find_optimal_speed(car_specs, start_lat, start_lon, end_lat, end_lon, ors_key, weather_key, current_battery_percent=100):
    SAFE_BATTERY_LIMIT = 5.0 
    
    print("\n[OPTIMIZER] Fetching Map and Weather Data...")
    route_data = get_route_data(start_lon, start_lat, end_lon, end_lat, ors_key)
    if route_data.get("status") != "success":
        return {"status": "failed", "message": "Could not get map data."}
        
    weather_data = get_weather_data(start_lat, start_lon, weather_key)
    if weather_data.get("status") != "success":
        return {"status": "failed", "message": "Could not get weather data."}

    print("[OPTIMIZER] Initializing Speed Simulation...")
    
    for test_speed in range(100, 35, -5):
        print(f"[OPTIMIZER] Simulating trip at {test_speed} km/h...")
        results = calculate_true_range(
            car_specs=car_specs, 
            route=route_data, 
            weather=weather_data, 
            target_speed_kmh=test_speed,
            current_battery_percent=current_battery_percent
        )
        if results.get("status") == "success":
            battery_left = results["battery_left_percent"]
            if battery_left >= SAFE_BATTERY_LIMIT:
                return {
                    "status": "success",
                    "recommended_speed_kmh": test_speed,
                    "estimated_arrival_battery": round(battery_left, 1),
                    "battery_left_percent": battery_left,
                    "total_energy_kwh": results["energy_used_kwh"],
                    "regen_saved_kwh": results.get("regen_saved_kwh", 0),
                    "total_distance_km": results["total_distance_km"],
                    "weather_used": results["weather_used"],
                    "3d_path": results["3d_path"], 
                    "surface_data": route_data.get("surface_data", {}) 
                }
    
    return {
        "status": "failed",
        "message": "DESTINATION UNREACHABLE. Even at 40 km/h, you will run out of battery."
    }