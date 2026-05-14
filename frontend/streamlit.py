import streamlit as st
import requests
import folium
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(page_title="FluxDrive", layout="wide")


def load_css():
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

if "page" not in st.session_state:
    st.session_state.page = "home"

if "result" not in st.session_state:
    st.session_state.result = None

if "dashboard_tab" not in st.session_state:
    st.session_state.dashboard_tab = "Route Planner"
if "dashboard_tab" not in st.session_state:
    st.session_state.dashboard_tab = "Route Planner"

if "selected_route_index" not in st.session_state:
    st.session_state.selected_route_index = 0


def get_route_coordinates(result):
    route_points = result.get("route_points", [])

    route_coordinates = [
        [point["lat"], point["lon"]]
        for point in route_points
        if "lat" in point and "lon" in point
    ]

    return route_coordinates
def get_selected_route(result):

    routes = result.get("routes", [])

    if not routes:
        return {}

    index = st.session_state.selected_route_index

    if index >= len(routes):
        index = 0
        st.session_state.selected_route_index = 0

    return routes[index]

def show_sidebar(result):
    car_model = result.get("car_model", "EV")
    battery_left = result.get("battery_left_percent", 0)

    with st.sidebar:
        st.markdown("## ⚡ FluxDrive")
        st.caption("Smarter Routes. More Range.")

        st.divider()

        if st.button("Route Planner", use_container_width=True):
            st.session_state.dashboard_tab = "Route Planner"
            st.rerun()

        if st.button("Map View", use_container_width=True):
            st.session_state.dashboard_tab = "Map View"
            st.rerun()

        if st.button("Analysis", use_container_width=True):
            st.session_state.dashboard_tab = "Analysis"
            st.rerun()

        if st.button("Settings", use_container_width=True):
            st.session_state.dashboard_tab = "Settings"
            st.rerun()

        st.divider()

        if st.button("← Back to Planner", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.dashboard_tab = "Route Planner"
            st.rerun()


def show_route_planner(result):
    routes = result.get("routes", [])

    if not routes:
        st.error("No routes available.")
        return

    # Get backend data for the analysis panel
    selected_idx = st.session_state.selected_route_index
    selected_route = routes[selected_idx]
    
    car_model = result.get("car_model", "Tesla Model 3")
    start_battery = result.get("input_battery_percentage", 0)
    
    # Real data from backend
    arrival_battery = selected_route.get("battery_left_percent", 0)
    rec_speed = selected_route.get("recommended_speed_kmh", 100)
    dist = selected_route.get("total_distance_km", 0)
    dur = selected_route.get("duration_min", 0)
    energy = selected_route.get("total_energy_kwh", 0)
    regen = selected_route.get("regen_saved_kwh", 0)

    source = result.get("source", "Source").title()
    destination = result.get("destination", "Destination").title()

    # --- TWO COLUMN LAYOUT (Map on Left, Analysis on Right) ---
    map_col, analysis_col = st.columns([1.8, 1])

    with map_col:
        st.markdown(f"## {source} to {destination}")
        
        source_coords = result.get("source_coordinates", {})
        dest_coords = result.get("destination_coordinates", {})

        m = folium.Map(
            location=[(source_coords.get("lat", 0) + dest_coords.get("lat", 0)) / 2, 
                      (source_coords.get("lon", 0) + dest_coords.get("lon", 0)) / 2],
            zoom_start=9,
            tiles="CartoDB dark_matter"
        )

        folium.Marker([source_coords.get("lat"), source_coords.get("lon")], icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([dest_coords.get("lat"), dest_coords.get("lon")], icon=folium.Icon(color="red")).add_to(m)

        # Plot all routes
        route_colors = ["#39ff14", "#1e90ff", "#ff9800"]
        for i, route in enumerate(routes):
            coords = route.get("3d_path", [])
            latlon = [[p[1], p[0]] for p in coords]
            if latlon:
                folium.PolyLine(
                    locations=latlon,
                    color=route_colors[i % len(route_colors)],
                    weight=7 if i == selected_idx else 3,
                    opacity=1 if i == selected_idx else 0.5
                ).add_to(m)

        st_folium(m, width=None, height=560)

    with analysis_col:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="analysis-header">Route Analysis</div>
            
            <div class="stat-box">
                <div class="metric-label">{car_model} • Start: {start_battery}%</div>
                <div style="margin-top:10px; font-weight:600;">Predicted Battery at Arrival</div>
                <div class="big-arrival-text">{arrival_battery}%</div>
                <div style="height:8px; background:#1e293b; border-radius:4px; margin: 10px 0;">
                    <div style="width:{arrival_battery}%; height:100%; background:#22c55e; border-radius:4px;"></div>
                </div>
                <div style="color:#22c55e; font-size:12px;">✔ Good for this trip!</div>
            </div>

            <div class="stat-box">
                <div class="metric-label">Recommended Speed</div>
                <div class="speed-gauge">{rec_speed} <span style="font-size:16px;">km/h</span></div>
                <div style="text-align:center; color:#94a3b8; font-size:12px;">Optimal for efficiency</div>
            </div>

            <div class="stat-box">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <div>
                        <div class="metric-label">Total Distance</div>
                        <div class="metric-value">{dist} km</div>
                    </div>
                    <div>
                        <div class="metric-label">Total Duration</div>
                        <div class="metric-value">{dur} min</div>
                    </div>
                    <div>
                        <div class="metric-label">Energy Used</div>
                        <div class="metric-value">{energy} kWh</div>
                    </div>
                    <div>
                        <div class="metric-label">Regen</div>
                        <div class="metric-value" style="color:#22c55e;">+{regen} kWh</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Route Comparison section remains below the map/analysis split
    st.markdown("### Route Comparison")
    comp_cols = st.columns(len(routes))
    for i, route in enumerate(routes):
        with comp_cols[i]:
            with st.container(border=True):
                st.write(f"Route {i+1}")
                st.write(f"**{route.get('battery_left_percent')}%** left")
                if st.button(f"Select Route {i+1}", key=f"sel_{i}", use_container_width=True):
                    st.session_state.selected_route_index = i
                    st.rerun()

def show_analysis(result):
    battery_left = result.get("battery_left_percent", "N/A")
    energy_used = result.get("energy_used_kwh", "N/A")
    distance = result.get("distance_km", "N/A")
    weather = result.get("weather_used", "N/A")
    risk = result.get("risk_level", "N/A")
    message = result.get("message", "N/A")
    input_battery = result.get("input_battery_percentage", "N/A")
    route_points = result.get("route_points", [])

    st.markdown("## 📊 Route Analysis")

    top_left, top_right = st.columns([1.1, 1])

    with top_left:
        with st.container(border=True):
            st.markdown("### Predicted Battery at Arrival")
            st.markdown(f"<div class='big-battery'>{battery_left}%</div>", unsafe_allow_html=True)
            st.progress(float(battery_left) / 100)
            st.success(message)

    with top_right:
        with st.container(border=True):
            st.markdown("### Trip Summary")

            a, b = st.columns(2)
            a.metric("Distance", f"{distance} km")
            b.metric("Energy Used", f"{energy_used} kWh")

            c, d = st.columns(2)
            c.metric("Start Battery", f"{input_battery}%")
            d.metric("Risk", risk)

            st.caption(f"Weather used: {weather}")

    st.markdown("### Energy Breakdown")

    b1, b2, b3 = st.columns(3)

    with b1:
        with st.container(border=True):
            st.markdown("#### 🚗 Driving Load")
            st.metric("Distance", f"{distance} km")
            st.caption("Base energy needed to move the vehicle.")

    with b2:
        with st.container(border=True):
            st.markdown("#### 🌦 Weather Impact")
            st.metric("Weather", weather)
            st.caption("Temperature and wind affect battery usage.")

    with b3:
        with st.container(border=True):
            st.markdown("#### 🔋 Battery Usage")
            try:
                used_percent = round(float(input_battery) - float(battery_left), 1)
            except:
                used_percent = "N/A"

            st.metric("Battery Used", f"{used_percent}%")
            st.caption("Predicted battery consumed during trip.")

    st.markdown("### Route Elevation Profile")

    with st.container(border=True):
        if route_points and "elevation" in route_points[0]:
            elevation_df = pd.DataFrame(route_points)
            elevation_df["point"] = range(len(elevation_df))

            st.line_chart(
                elevation_df,
                x="point",
                y="elevation",
                use_container_width=True
            )
        else:
            st.info("Elevation data not available.")


  
def show_map_view(result):
    st.markdown("## 🗺️ Interactive Map View")

    routes = result.get("routes", [])
    if not routes:
        st.error("No routes available to map.")
        return

    source = result.get("source", "Source").title()
    destination = result.get("destination", "Destination").title()

    source_coords = result.get("source_coordinates", {})
    destination_coords = result.get("destination_coordinates", {})

    source_lat = source_coords.get("lat")
    source_lon = source_coords.get("lon")
    dest_lat = destination_coords.get("lat")
    dest_lon = destination_coords.get("lon")

    if not source_lat or not source_lon or not dest_lat or not dest_lon:
        st.warning("Coordinates not available for mapping.")
        return

    center_lat = (source_lat + dest_lat) / 2
    center_lon = (source_lon + dest_lon) / 2

    # Create a full-screen optimized map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="CartoDB dark_matter"
    )

    # Add Markers
    folium.Marker(
        [source_lat, source_lon],
        tooltip=f"Start: {source}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        [dest_lat, dest_lon],
        tooltip=f"End: {destination}",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)

    route_colors = ["#39ff14", "#1e90ff", "#ff9800"]
    all_points = []

    for i, route in enumerate(routes):
        coords = route.get("coordinates_3d", route.get("3d_path", []))
        latlon = []

        for point in coords:
            if len(point) >= 2:
                lon = point[0]
                lat = point[1]
                latlon.append([lat, lon])

        if latlon:
            all_points.extend(latlon)
            folium.PolyLine(
                locations=latlon,
                color=route_colors[i % len(route_colors)],
                weight=5,
                opacity=0.8,
                tooltip=f"Route {i + 1}"
            ).add_to(m)

    if all_points:
        m.fit_bounds(all_points)

    # Render a large map specifically for this view
    with st.container(border=True):
        st_folium(m, width=None, height=600)

def show_placeholder_page(title):
    st.title(title)
    st.info("This page can be developed later.")


def show_result_page():
    result = st.session_state.result

    show_sidebar(result)

    tab = st.session_state.dashboard_tab

    if tab == "Route Planner":
        show_route_planner(result)

    elif tab == "Map View":
        show_map_view(result)

    elif tab == "Analysis":
        show_analysis(result)

    elif tab == "Trips":
        show_placeholder_page("🧳 Trips")

    elif tab == "Vehicle Profile":
        show_placeholder_page("🚗 Vehicle Profile")

    elif tab == "Settings":
        show_placeholder_page("⚙ Settings")


if st.session_state.page == "result":
    show_result_page()
    st.stop()


st.markdown("""
<div class="navbar">
    <div class="logo">⚡ FluxDrive</div>
    <div class="navlinks">
        <span class="active">Home</span>
        <span>Vehicles</span>
        <span class="nav-btn">Plan My Trip</span>
    </div>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.1, 1])

with left:
    st.markdown("""
    <div class="hero-text">
        <h1>Plan Smarter.<br>Drive Further.</h1>
        <p>
            Real-Time Route, Weather, & Terrain Intelligence<br>
            To Predict Your EV’s True Range.
        </p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛣️</div>
            <b>Smart Route<br>Optimization</b>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌧️</div>
            <b>Real-time<br>Weather</b>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔋</div>
            <b>Accurate Range<br>Prediction</b>
        </div>
        """, unsafe_allow_html=True)

with right:
    st.markdown('<div class="form-heading">Plan Your Trip</div>', unsafe_allow_html=True)

    # Labels visible above, boxes styled as steel grey below
    source = st.text_input("From", placeholder="Enter starting location", label_visibility="visible")
    
    destination = st.text_input("To", placeholder="Enter destination", label_visibility="visible")
    
    vehicle = st.selectbox(
        "Select Vehicle",
        ["Choose your EV", "Tesla Model 3", "Tata Nexon EV", "BYD Atto 3"],
        label_visibility="visible"
    )

    # Fixed: You can now click and type in this box
    battery = st.number_input(
        "Battery Percentage (%)",
        min_value=0,
        max_value=100,
        value=80,
        label_visibility="visible"
    )

    calculate = st.button("Calculate Range ❯", use_container_width=True)
if calculate:
    if not source or not destination:
        st.error("Please enter both From and To locations.")

    elif vehicle == "Choose your EV":
        st.error("Please select a vehicle.")

    elif battery <= 0:
        st.error("Please enter battery percentage.")

    else:
        api_url = "http://127.0.0.1:8000/getdata/"

        payload = {
            "Source": source,
            "Destination": destination,
            "Car_Model": vehicle,
            "Battery_percentage": battery
        }

        try:
            response = requests.post(api_url, data=payload)

            if response.status_code == 200:
                result = response.json()
                print(result)
                routes = result.get("routes", [])
                selected_route = routes[0] if routes else {}

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.result = result
                    st.session_state.page = "result"
                    st.session_state.dashboard_tab = "Route Planner"
                    st.rerun()

            else:
                st.error(f"Backend error: {response.status_code}")
                st.write(response.text)

        except Exception as e:
            st.error("Could not connect to backend.")
            st.write(e)

st.markdown('</div>', unsafe_allow_html=True)