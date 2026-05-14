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

    source = result.get("source", "Source").title()
    destination = result.get("destination", "Destination").title()

    route_colors = ["#39ff14", "#1e90ff", "#ff9800"]
    route_titles = ["Recommended", "Energy Saver", "Fastest"]

    st.markdown("## Route Planner")

    top1, top2 = st.columns(2)
    top1.metric("From", source)
    top2.metric("To", destination)

    source_coords = result.get("source_coordinates", {})
    destination_coords = result.get("destination_coordinates", {})

    source_lat = source_coords.get("lat")
    source_lon = source_coords.get("lon")
    dest_lat = destination_coords.get("lat")
    dest_lon = destination_coords.get("lon")

    if not source_lat or not source_lon or not dest_lat or not dest_lon:
        st.warning("Coordinates not available.")
        return

    center_lat = (source_lat + dest_lat) / 2
    center_lon = (source_lon + dest_lon) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=9,
        tiles="CartoDB dark_matter"
    )

    folium.Marker(
        [source_lat, source_lon],
        tooltip=f"Source: {source}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        [dest_lat, dest_lon],
        tooltip=f"Destination: {destination}",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)

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
                weight=7 if i == st.session_state.selected_route_index else 4,
                opacity=1 if i == st.session_state.selected_route_index else 0.55,
                tooltip=f"Route {i + 1}"
            ).add_to(m)

    if all_points:
        m.fit_bounds(all_points)

    st_folium(m, width=None, height=360)

    st.markdown("### Route Comparison")

    if len(routes) == 1:
        comparison_cols = st.columns([1, 1.4, 1])
        usable_cols = [comparison_cols[1]]
    elif len(routes) == 2:
        comparison_cols = st.columns([1, 1, 1.2])
        usable_cols = comparison_cols[:2]
    else:
        usable_cols = st.columns(3)

    for i, route in enumerate(routes):
        with usable_cols[i]:
            with st.container(border=True):
                title = route_titles[i] if i < len(route_titles) else f"Route {i + 1}"

                battery_left = route.get("battery_left_percent", "N/A")
                distance = route.get("total_distance_km", route.get("distance_km", "N/A"))
                duration = route.get("duration_min", "N/A")
                energy = route.get("total_energy_kwh", "N/A")
                coords = route.get("coordinates_3d", route.get("3d_path", []))

                elevation_status = "Moderate"
                elevations = [p[2] for p in coords if len(p) >= 3]

                if elevations:
                    elevation_range = max(elevations) - min(elevations)

                    if elevation_range < 100:
                        elevation_status = "Low"
                    elif elevation_range < 300:
                        elevation_status = "Moderate"
                    else:
                        elevation_status = "High"

                road_quality = "Good"
                surface_values = route.get("surface_data", {}).get("values", [])

                if surface_values:
                    bad_surface_count = 0

                    for block in surface_values:
                        if block[2] in [1, 4]:
                            bad_surface_count += 1

                    if bad_surface_count == 0:
                        road_quality = "Good"
                    elif bad_surface_count <= 2:
                        road_quality = "Moderate"
                    else:
                        road_quality = "Poor"

                traffic_status = "Moderate"
                road_values = route.get("road_type_data", {}).get("values", [])

                if road_values:
                    city_road_count = 0

                    for block in road_values:
                        if block[2] == 2:
                            city_road_count += 1

                    if city_road_count == 0:
                        traffic_status = "Light"
                    elif city_road_count <= 2:
                        traffic_status = "Moderate"
                    else:
                        traffic_status = "Heavy"

                st.markdown(f"#### {title}")
                st.caption(f"{distance} km • {duration} min")

                st.markdown(
                    f"""
                    <div style="font-size:30px;font-weight:900;color:{route_colors[i % len(route_colors)]};line-height:1;">
                        {battery_left}%
                    </div>
                    <div style="font-size:12px;color:#9ca3af;margin-bottom:8px;">
                        battery left
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                graph_rows = []

                for j, point in enumerate(coords):
                    if len(point) >= 3:
                        graph_rows.append({
                            "point": j,
                            "elevation": point[2]
                        })

                if graph_rows:
                    graph_df = pd.DataFrame(graph_rows)

                    st.line_chart(
                        graph_df,
                        x="point",
                        y="elevation",
                        height=120,
                        use_container_width=True
                    )
                else:
                    st.caption("Graph unavailable")

                c1, c2 = st.columns(2)
                c1.caption("Elevation")
                c1.write(elevation_status)

                c2.caption("Traffic")
                c2.write(traffic_status)

                c3, c4 = st.columns(2)
                c3.caption("Road Quality")
                c3.write(road_quality)

                c4.caption("Energy")
                c4.write(f"{energy} kWh")

                if i == st.session_state.selected_route_index:
                    st.success("Selected")
                else:
                    if st.button("Select Route", key=f"select_route_{i}", use_container_width=True):
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
<div class="landing-page">

    <div class="navbar">
        <div class="logo">⚡ FluxDrive</div>
        <div class="navlinks">
            <span class="active">Home</span>
            <span>Vehicles</span>
            <span class="nav-btn">Plan My Trip</span>
        </div>
    </div>

</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.1, 1])

with left:
    st.markdown("""
    <div class="hero-text">
        <h1>Plan Smarter.<br>Drive Further.</h1>
        <p>
        Real-time route + weather + terrain intelligence<br>
        to predict your EV’s true range.
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
    st.markdown("""
    <div class="form-heading">Plan Your Trip</div>
    """, unsafe_allow_html=True)

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
        value=0
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