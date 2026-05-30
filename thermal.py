import requests
from datetime import datetime
def get_cabin_soak_temp(lat: float, lon: float) -> float:
    """
    Queries Open-Meteo for recent historical hourly temperatures at the starting 
    point, computes the ambient average, and applies greenhouse scale factor.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    param={
        "latitude":lat,"longitude":lon,"hourly":"temperature_2m","past_days":1,"forecast_days":1      }
    DEFAULT_CAR_TEMP=24.0
    try:
        response=requests.get(url,params=param,timeout=25)
        if response.status_code == 200:
            data=response.json()
            hourly_data=data.get("hourly", {})
            timestamps = hourly_data.get("time", [])
            temperatures = hourly_data.get("temperature_2m", [])
            if not temperatures:
                return DEFAULT_CAR_TEMP
            
            current_hour_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:00")

            try:
                current_index = timestamps.index(current_hour_iso)
                start_index = max(0, current_index - 3)
                recent_temps = temperatures[start_index : current_index + 1]
            except ValueError:
                recent_temps = temperatures[:4]

            if recent_temps:
                    avg_temp=sum(recent_temps)/len(recent_temps)
                    if avg_temp>24:
                        estimated_cabin_soak=avg_temp+(avg_temp-20.0)*0.8         #20 room temp and 0.8 thermal gain multiplier
                    else:
                        estimated_cabin_soak=avg_temp
                    return max(estimated_cabin_soak, avg_temp)   
    
    except Exception as e:
        print(f"[THERMAL ENGINE] API Handoff failure: {e}.")
    
    return DEFAULT_CAR_TEMP