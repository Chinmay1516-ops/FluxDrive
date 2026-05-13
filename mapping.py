import requests
def get_route_data(start_lon, start_lat, end_lon, end_lat, api_key):
    """
    Asks OpenRouteService for the driving route, elevation, AND road surface types.
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    body = {
        "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
        "elevation": True,
        "extra_info": ["surface", "waycategory"]
    }
    print("Fetching route and surface data from satellite...")
    response = requests.post(url, json=body, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        route_summary = data['features'][0]['properties']['summary']
        total_distance_km = route_summary['distance'] / 1000
        coordinates_3d = data['features'][0]['geometry']['coordinates']
        extras = data['features'][0]['properties'].get('extras', {})
        
        return {
            "status": "success",
            "distance_km": round(total_distance_km, 2),
            "3d_path": coordinates_3d,
            "surface_data": extras.get("surface", {}),       
            "road_type_data": extras.get("waycategory", {})
        }
    else:
        return {
            "status": "error",
            "message": f"Failed! Error Code: {response.status_code}",
            "details": response.text
        }