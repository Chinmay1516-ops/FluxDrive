# app/services/geocoding.py

import requests


def get_coordinates(place_name: str):
    url = "https://nominatim.openstreetmap.org/search"             #OpenStreetMap Nominatim API

    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "EcoRouteEV/1.0"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if len(data) == 0:
        return None

    first_result = data[0]

    return {
        "lat": float(first_result["lat"]),
        "lon": float(first_result["lon"])
    }
