import math
from physics import calculate_segment_energy, calculate_regen_energy


SURFACE_FRICTION = {
    0: 0.015,  
    1: 0.025,  
    2: 0.015,  
    3: 0.012,  
    4: 0.020,  
}


STOPS_PER_KM = {
    0: 0.0,  
    1: 0.5, 
    2: 2.0,  
    3: 0.0,  
}
MAX_COMPRESSOR_POWER_KW = 3.0
CABIN_TEMP_THRESHOLD = 30.0

def get_block_value(segment_index, blocks, default_val):
    if not blocks: return default_val 
    for block in blocks:
        if block[0] <= segment_index <= block[1]:
            return block[2]
    return default_val

def get_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_true_range(car_specs, route, weather, target_speed_kmh=70, current_battery_percent=100,outside_temp=25.0,initial_cabin_temp=24.0):
    wind_kmh = weather["wind_speed_kmh"]
    points = route["3d_path"]
    
    total_energy_kwh = 0.0
    total_regen_kwh = 0.0 
    
    surface_blocks = route.get("surface_data", {}).get("values", [])
    road_type_blocks = route.get("road_type_data", {}).get("values", [])
    route_distance_km = route["distance_km"]
    thermal_zone_km = route_distance_km * 0.15             #we want for 15%of our route
    cooling_constant_km = max(1.0, thermal_zone_km / 3)
    distance_travelled_km = 0.0                                # FIXED: Initialized distance tracker at 0 before the loop starts
    total_hvac_energy_kwh = 0.0                                                           
    
    
    for i in range(len(points) - 1):
        lon1, lat1, elev1 = points[i]
        lon2, lat2, elev2 = points[i+1]
        
        dist_km = get_distance_km(lat1, lon1, lat2, lon2)
        if dist_km == 0: continue 
            
        elev_change_meters = elev2 - elev1
        slope_percent = (elev_change_meters / (dist_km * 1000)) * 100

        surface_type = get_block_value(i, surface_blocks, 0)
        current_friction = SURFACE_FRICTION.get(surface_type, 0.015)

        segment_energy = calculate_segment_energy(
            distance_km=dist_km,
            slope_percent=slope_percent,
            speed_kmh=target_speed_kmh,
            headwind_kmh=wind_kmh,
            weight_kg=car_specs['weight_kg'],
            drag_coeff=car_specs['drag_coefficient'],
            frontal_area_m2=car_specs['frontal_area'],
            rolling_coeff=current_friction
        )
        total_energy_kwh += segment_energy
        if initial_cabin_temp > CABIN_TEMP_THRESHOLD and distance_travelled_km < thermal_zone_km:
            decay_factor = math.exp(-distance_travelled_km / cooling_constant_km)
            compressor_power_kw = MAX_COMPRESSOR_POWER_KW * decay_factor
            segment_time_hr = dist_km / target_speed_kmh
            segment_hvac_energy_kwh = compressor_power_kw * segment_time_hr
            total_energy_kwh += segment_hvac_energy_kwh
            total_hvac_energy_kwh += segment_hvac_energy_kwh

        road_category = get_block_value(i, road_type_blocks, 0)
        expected_stops_per_km = STOPS_PER_KM.get(road_category, 0.0)
        stops_in_this_segment = dist_km * expected_stops_per_km
        
        if stops_in_this_segment > 0:
            regen_per_stop = calculate_regen_energy(car_specs['weight_kg'], target_speed_kmh)
            regen_for_segment = regen_per_stop * stops_in_this_segment
            total_regen_kwh += regen_for_segment
            total_energy_kwh -= regen_for_segment
        distance_travelled_km += dist_km 
        
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
        "regen_saved_kwh": round(total_regen_kwh, 2),
        "hvac_spent_kwh": round(total_hvac_energy_kwh, 2),
        "thermal_soak_cabin_temp": round(initial_cabin_temp, 1), 
        "battery_left_percent": round(percent_left, 1),
        "3d_path": route["3d_path"]
    }