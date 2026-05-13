from engine import calculate_true_range
def find_optimal_speed(car_specs, start_lat, start_lon, end_lat, end_lon, ors_key, weather_key, current_battery_percent=100):
    SAFE_BATTERY_LIMIT = 5.0 
    
    print("\n[OPTIMIZER] Initializing Speed Simulation...")
    
    for test_speed in range(100, 35, -5):
        print(f"[OPTIMIZER] Simulating trip at {test_speed} km/h...")
        results = calculate_true_range(
            car_specs, start_lat, start_lon, end_lat, end_lon, 
            ors_key, weather_key, target_speed_kmh=test_speed,
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
                    "total_distance_km": results["total_distance_km"],
                    "weather_used": results["weather_used"],
                    "3d_path": results["3d_path"] 
                }
    
    return {
        "status": "failed",
        "message": "DESTINATION UNREACHABLE. Even at 40 km/h, you will run out of battery."
    }