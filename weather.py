import requests
def get_weather_data(lat, lon, api_key):
    """
    Fetches live weather data (wind speed and temperature) for a specific coordinate.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    print("Fetching live weather from satellites...")
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        wind_speed_ms = data['wind']['speed']
        wind_speed_kmh = wind_speed_ms * 3.6
        temperature_c = data['main']['temp']
        return {
            "status": "success",
            "temperature_c": round(temperature_c, 1),
            "wind_speed_kmh": round(wind_speed_kmh, 1)
        }
    else:
        return {
            "status": "error",
            "message": f"Weather API Failed! Error Code: {response.status_code}",
            "details": response.text
        }