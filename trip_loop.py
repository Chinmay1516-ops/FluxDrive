from physics import calculate_segment_energy
def calculate_full_trip(car_specs, route_segments):
    """
    Takes a car and a list of road segments, loops through them, 
    and calculates the total battery drain.
    """
    total_energy_used_kwh = 0.0
    for segment in route_segments:
        energy_for_this_segment = calculate_segment_energy(
            distance_km=segment['distance_km'],
            slope_percent=segment['slope_percent'],
            speed_kmh=segment['speed_kmh'],
            headwind_kmh=segment['headwind_kmh'],
            weight_kg=car_specs['weight_kg'],
            drag_coeff=car_specs['drag_coefficient'],
            frontal_area_m2=car_specs['frontal_area']
        )
        total_energy_used_kwh += energy_for_this_segment
    battery_capacity = car_specs['battery_capacity_kwh']
    remaining_battery_kwh = battery_capacity - total_energy_used_kwh
    if remaining_battery_kwh < 0:
        remaining_battery_kwh = 0
    percentage_left = (remaining_battery_kwh / battery_capacity) * 100
    
    return {
        "total_kwh_used": round(total_energy_used_kwh, 2),
        "kwh_remaining": round(remaining_battery_kwh, 2),
        "percentage_left": round(percentage_left, 1)
    }