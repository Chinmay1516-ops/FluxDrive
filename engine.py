import math
from physics import calculate_segment_energy
from mapping import get_route_data
from weather import get_weather_data
def get_distance_km(lat1, lon1, lat2, lon2):
    """ Converts GPS coordinates into real-world kilometers (Haversine formula) """
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
def calculate_true_range(car_specs, start_lat, start_lon, end_lat, end_lon, ors_key, weather_key, target_speed_kmh=70, current_battery_percent=100):
    """ Combines Maps, Weather, and Physics. """
    route = get_route_data(start_lon, start_lat, end_lon, end_lat, ors_key)
    if route["status"] != "success":
        return {"error": "Could not get map data."}
    weather = get_weather_data(start_lat, start_lon, weather_key)
    if weather["status"] != "success":
        return {"error": "Could not get weather data."}
    wind_kmh = weather["wind_speed_kmh"]
    points = route["3d_path"]
    total_energy_kwh = 0.0
    
    print(f"Adaptive Terrain Computation for {len(points)} road segments...")
    
    for i in range(len(points) - 1):
        lon1, lat1, elev1 = points[i]
        lon2, lat2, elev2 = points[i+1]
        
        dist_km = get_distance_km(lat1, lon1, lat2, lon2)
        if dist_km == 0:
            continue 
        elev_change_meters = elev2 - elev1
        slope_percent = (elev_change_meters / (dist_km * 1000)) * 100

        segment_energy = calculate_segment_energy(
            distance_km=dist_km,
            slope_percent=slope_percent,
            speed_kmh=target_speed_kmh,
            headwind_kmh=wind_kmh,
            weight_kg=car_specs['weight_kg'],
            drag_coeff=car_specs['drag_coefficient'],
            frontal_area_m2=car_specs['frontal_area']
        )
        total_energy_kwh += segment_energy
    battery_size = car_specs['battery_capacity_kwh']
    starting_kwh = battery_size * (current_battery_percent / 100)
    remaining_kwh = starting_kwh - total_energy_kwh
    
    if remaining_kwh < 0: remaining_kwh = 0
    percent_left = (remaining_kwh / battery_size) * 100
    
    return {
        "status": "success",
        "total_distance_km": route["distance_km"],
        "weather_used": f"{weather['temperature_c']}°C, Wind: {wind_kmh}km/h",
        "energy_used_kwh": round(total_energy_kwh, 2),
        "battery_left_percent": round(percent_left, 1),
        "3d_path": route["3d_path"]
    }