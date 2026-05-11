import math

def calculate_segment_energy(distance_km, slope_percent, speed_kmh, headwind_kmh, weight_kg, drag_coeff, frontal_area_m2):
    """
    Calculates the energy required (in kWh) to travel a specific segment of road.
    """
    
    GRAVITY = 9.81            
    AIR_DENSITY = 1.225      
    ROLLING_COEFF = 0.015   

    distance_m = distance_km * 1000
    speed_ms = speed_kmh / 3.6
    wind_ms = headwind_kmh / 3.6
    theta = math.atan(slope_percent / 100.0)

    f_drag = 0.5 * AIR_DENSITY * drag_coeff * frontal_area_m2 * (speed_ms + wind_ms)**2
    f_gravity = weight_kg * GRAVITY * math.sin(theta)
    f_rolling = ROLLING_COEFF * weight_kg * GRAVITY * math.cos(theta)
    total_force = f_drag + f_gravity + f_rolling
   
    energy_joules = total_force * distance_m
    
    energy_kwh = energy_joules / 3600000.0
    return energy_kwh
