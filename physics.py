import math

def calculate_segment_energy(distance_km, slope_percent, speed_kmh, headwind_kmh, weight_kg, drag_coeff, frontal_area_m2, rolling_coeff=0.015):
    """
    Calculates the energy required (in kWh) to travel a specific segment of road.
    """
    
    GRAVITY = 9.81            
    AIR_DENSITY = 1.225      

    distance_m = distance_km * 1000
    speed_ms = speed_kmh / 3.6
    wind_ms = headwind_kmh / 3.6
    theta = math.atan(slope_percent / 100.0)

    f_drag = 0.5 * AIR_DENSITY * drag_coeff * frontal_area_m2 * (speed_ms + wind_ms)**2
    f_gravity = weight_kg * GRAVITY * math.sin(theta)
    
    
    f_rolling = rolling_coeff * weight_kg * GRAVITY * math.cos(theta)
    
    total_force = f_drag + f_gravity + f_rolling
   
    energy_joules = total_force * distance_m
    
    energy_kwh = energy_joules / 3600000.0
    return energy_kwh

def calculate_regen_energy(weight_kg, current_speed_kmh, target_speed_kmh=10, efficiency=0.65):
    """
    Calculates the energy (kWh) recovered through regenerative braking 
    when the car slows down for a speed bump or traffic light.
    """
    if current_speed_kmh <= target_speed_kmh: 
        return 0.0
    v_initial = current_speed_kmh / 3.6
    v_final = target_speed_kmh / 3.6
    ke_initial = 0.5 * weight_kg * (v_initial ** 2)
    ke_final = 0.5 * weight_kg * (v_final ** 2)
    energy_joules_lost = ke_initial - ke_final
    energy_recovered_joules = energy_joules_lost * efficiency
    return energy_recovered_joules / 3600000.0