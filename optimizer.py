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
    optimised_routes=[]
    for route in route_data["routes"]:
      for test_speed in range(100, 35, -5):
        print(
    f"[OPTIMIZER] Simulating trip at "
    f"{test_speed} km/h..."
    f" Route {route['route_id']}"
)
        results = calculate_true_range(
            car_specs=car_specs, 
            route=route, 
            weather=weather_data, 
            target_speed_kmh=test_speed,
            current_battery_percent=current_battery_percent
        )
        if results.get("status") == "success":
            battery_left = results["battery_left_percent"]
            if battery_left >= SAFE_BATTERY_LIMIT:
                optimised_routes.append({
                   "route_id": route["route_id"],
                    "status": "success",
                    "recommended_speed_kmh": test_speed,
                    "estimated_arrival_battery": round(battery_left, 1),
                    "battery_left_percent": battery_left,
                    "total_energy_kwh": results["energy_used_kwh"],
                    "regen_saved_kwh": results.get("regen_saved_kwh", 0),
                    "total_distance_km": results["total_distance_km"],
                    "weather_used": results["weather_used"],
                    "3d_path": results.get("3d_path", route.get("3d_path", [])),
                    "coordinates_3d":route.get("coordinates_3d",[]),
                    "road_type_data": route.get("road_type_data", {}), 
                    "directions": route.get("directions", []),
                    "duration_min": route.get("duration_min"),
                    "surface_data": route.get("surface_data", {})  
                })
                break
    if len(optimised_routes) == 0:

     return {
        "status": "failed",
        "message": "DESTINATION UNREACHABLE. Even at 40 km/h, you will run out of battery."
    }
    return{
       "status":"success", "routes":optimised_routes
    }