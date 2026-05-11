import requests
def get_route_data(start_lon, start_lat, end_lon, end_lat, api_key):
    """
    Asks OpenRouteService for the driving route and the elevation (hills) between two points.
    """
    
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    
    
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    body = {
        "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
        "elevation": True 
    }
    print("Fetching route from satellite...")
    response = requests.post(url, json=body, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        route_summary = data['features'][0]['properties']['summary']
        total_distance_km = route_summary['distance'] / 1000
        coordinates_3d = data['features'][0]['geometry']['coordinates']
        return {
            "status": "success",
            "distance_km": round(total_distance_km, 2),
            "3d_path": coordinates_3d
        }
    else:
        return {
            "status": "error",
            "message": f"Failed! Error Code: {response.status_code}",
            "details": response.text
        }