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
        "elevation": True,"instructions": True,
        "extra_info": ["surface", "waycategory"], 
    }
    print("Fetching route and surface data from satellite...")
    response = requests.post(url, json=body, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        first_route = data['features'][0]
        first_summary = first_route['properties']['summary']
        total_distance_km = first_summary['distance'] / 1000
        print(f"Primary route distance: {round(total_distance_km,2)} km")
        if total_distance_km < 100:
           print("Distance <100km → requesting alternative routes...") 
           body["alternative_routes"] = {"target_count": 2, "share_factor": 0.3,"weight_factor": 2.0}
           response = requests.post(url, json=body, headers=headers, timeout=10)
            
           if response.status_code == 200:
                data = response.json()

        two_routes = []

        for i, feature in enumerate(data["features"]):
            route_summary = feature['properties']['summary']
            extras = feature['properties'].get('extras', {})

            directions = []

            segments = feature["properties"].get("segments", [])

            if segments:
                for step in segments[0].get("steps", []):

                    directions.append({
                        "instruction": step.get("instruction", ""),
                        "distance_km": round(step.get("distance", 0) / 1000, 2),
                        "duration_min": round(step.get("duration", 0) / 60, 1)
                    })

            two_routes.append({
                "route_id": i + 1,
                "route_summary": route_summary,
                "distance_km": round(route_summary['distance'] / 1000, 2),
                "total_distance_km": round(route_summary['distance'] / 1000, 2),
                "duration_min": round(route_summary['duration'] / 60, 1),
                "3d_path": feature['geometry']['coordinates'],
                "coordinates_3d": feature['geometry']['coordinates'],
                "extras": extras,
                "surface_data": extras.get("surface", {}),       
                "road_type_data": extras.get("waycategory", {}),
                "directions": directions
            })
        
        return {
            "status": "success",
            "routes": two_routes
        }

    else:
        return {
            "status": "error",
            "message": f"Failed! Error Code: {response.status_code}",
            "details": response.text
        }