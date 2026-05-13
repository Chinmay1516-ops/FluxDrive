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


def get_route_coordinates(result):
    route_points = result.get("route_points", [])

    route_coordinates = [
        [point["lat"], point["lon"]]
        for point in route_points
        if "lat" in point and "lon" in point
    ]

    return route_coordinates


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

        if st.button("Trips", use_container_width=True):
            st.session_state.dashboard_tab = "Trips"
            st.rerun()

        if st.button("Vehicle Profile", use_container_width=True):
            st.session_state.dashboard_tab = "Vehicle Profile"
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
    source = result.get("source", "Source").title()
    destination = result.get("destination", "Destination").title()
    car_model = result.get("car_model", "EV")
    distance = result.get("distance_km", "N/A")
    energy_used = result.get("energy_used_kwh", "N/A")
    battery_left = result.get("battery_left_percent", "N/A")
    weather = result.get("weather_used", "N/A")
    risk = result.get("risk_level", "N/A")
    message = result.get("message", "N/A")
    input_battery = result.get("input_battery_percentage", "N/A")

    st.title("⚡ FluxDrive Route Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("From", source)
    c2.metric("To", destination)
    c3.metric("Vehicle", car_model)
    c4.metric("Start Battery", f"{input_battery}%")

    st.divider()

    m1, m2, m3 = st.columns(3)
    m1.metric("Distance", f"{distance} km")
    m2.metric("Energy Used", f"{energy_used} kWh")
    m3.metric("Battery Left", f"{battery_left}%")

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Trip Recommendation")
        if risk == "high":
            st.error(message)
        else:
            st.success(message)

        st.write(
            f"Your trip from **{source}** to **{destination}** is approximately "
            f"**{distance} km**. The model predicts **{energy_used} kWh** energy usage."
        )

    with right:
        st.subheader("Quick Details")
        st.write(f"**Weather Used:** {weather}")
        st.write(f"**Risk Level:** {risk}")
        st.write(f"**Arrival Battery:** {battery_left}%")

        try:
            st.progress(float(battery_left) / 100)
        except:
            st.progress(0)


def show_map_view(result):
    source = result.get("source", "Source").title()
    destination = result.get("destination", "Destination").title()

    source_coords = result.get("source_coordinates", {})
    destination_coords = result.get("destination_coordinates", {})

    source_lat = source_coords.get("lat")
    source_lon = source_coords.get("lon")
    dest_lat = destination_coords.get("lat")
    dest_lon = destination_coords.get("lon")

    route_coordinates = get_route_coordinates(result)

    st.title("🗺 Map View")
    st.caption("Real road route using backend route points")

    if not source_lat or not source_lon or not dest_lat or not dest_lon:
        st.warning("Coordinates not available from backend.")
        return

    center_lat = (source_lat + dest_lat) / 2
    center_lon = (source_lon + dest_lon) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles="CartoDB dark_matter"
    )

    folium.Marker(
        [source_lat, source_lon],
        popup=source,
        tooltip=f"Source: {source}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        [dest_lat, dest_lon],
        popup=destination,
        tooltip=f"Destination: {destination}",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)

    if route_coordinates:
        folium.PolyLine(
            locations=route_coordinates,
            color="#39ff14",
            weight=6,
            opacity=0.9,
            tooltip="Real road route"
        ).add_to(m)

        m.fit_bounds(route_coordinates)

    else:
        folium.PolyLine(
            locations=[
                [source_lat, source_lon],
                [dest_lat, dest_lon]
            ],
            color="#39ff14",
            weight=6,
            opacity=0.9,
            tooltip="Approx route"
        ).add_to(m)

    st_folium(m, width=1100, height=600)


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

st.markdown('<div class="hero-section">', unsafe_allow_html=True)

left, right = st.columns([1.2, 1])

with left:
    st.markdown("""
    <div class="hero-text">
        <h1>Plan Smarter.<br><span>Drive Further.</span></h1>
        <p>Real-time route + weather + terrain intelligence<br>
        to predict your EV’s true range.</p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🛣️</div>
            <b>Smart Route<br>Optimization</b>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🌧️</div>
            <b>Real-time<br>Weather</b>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🔋</div>
            <b>Accurate Range<br>Prediction</b>
        </div>
        """, unsafe_allow_html=True)

with right:
    with st.container():
        st.markdown('<div class="form-title">Plan Your Trip</div>', unsafe_allow_html=True)

        source = st.text_input("From", placeholder="Enter starting location")
        destination = st.text_input("To", placeholder="Enter destination")

        vehicle = st.selectbox(
            "Select Vehicle",
            ["Choose your EV", "Tesla Model 3", "Tata Nexon EV", "BYD Atto 3"]
        )

        battery = st.number_input(
            "Battery Percentage (%)",
            min_value=0,
            max_value=100,
            value=80
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