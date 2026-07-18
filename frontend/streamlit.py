import os
import sys
import asyncio

# This line tells Python to look in the main root folder for main.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import getdata
import streamlit as st
import requests
import folium
import pandas as pd
from streamlit_folium import st_folium
import altair as alt
import asyncio

st.set_page_config(page_title="FluxDrive", layout="wide")


def load_css():
    with open("frontend/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

if "page" not in st.session_state:
    st.session_state.page = "home"

if "result" not in st.session_state:
    st.session_state.result = None

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

    meta_left, meta_right = st.columns(2)
    meta_left.markdown(f"**From:** {source} | **To:** {destination}")

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
    layout_map_col, layout_cards_col = st.columns([1.3, 1])
    with layout_map_col:
          st_folium(m, width=None, height=340,use_container_width=True)

    

    # if len(routes) == 1:
    #     comparison_cols = st.columns([1, 1.4, 1])
    #     usable_cols = [comparison_cols[1]]
    # elif len(routes) == 2:
    #     comparison_cols = st.columns([1, 1, 1.2])
    #     usable_cols = comparison_cols[:2]
    # else:
    #     usable_cols = st.columns(3)

    # for i, route in enumerate(routes):
    #     with usable_cols[i]:
    with layout_cards_col:
        st.markdown("### Options")
        for i, route in enumerate(routes):
           with st.container(border=True):
                current_color = route_colors[i % len(route_colors)]
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

                # 1. Combined Compact Header Layout
                st.markdown(f"##### {title} <span style='font-size:12px; color:#9ca3af; float:right;'>🛣️ {distance} km • ⏱️ {duration} min</span>", unsafe_allow_html=True)

                # 2. Rounded Battery Format (Fixes the long float issue)
                try:
                    formatted_battery = f"{float(battery_left):.1f}"
                except:
                    formatted_battery = "N/A"

                st.markdown(
                    f"""
                    <div style="margin: 4px 0 8px 0; display: flex; align-items: baseline; gap: 8px;">
                        <span style="font-size:24px; font-weight:900; color:{current_color}; line-height:1;">{formatted_battery}%</span>
                        <span style="font-size:10px; color:#9ca3af; text-transform: uppercase; font-weight:700; letter-spacing:0.3px;">battery left</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # 4. Streamlined Metrics Matrix Rows (Replaces c1, c2, c3, c4 column layout)
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 6px; margin-bottom: 12px; font-size: 12px;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.02); padding-bottom: 2px;">
                        <span style="color: #9ca3af;">⛰️ Elevation</span> 
                        <span style="font-weight: 700; color: #ffffff;">{elevation_status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.02); padding-bottom: 2px;">
                        <span style="color: #9ca3af;">🚦 Traffic</span> 
                        <span style="font-weight: 700; color: #ffffff;">{traffic_status}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.02); padding-bottom: 2px;">
                        <span style="color: #9ca3af;">🛠️ Road Quality</span> 
                        <span style="font-weight: 700; color: #ffffff;">{road_quality}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #9ca3af;">⚡ Net Energy</span> 
                        <span style="font-weight: 700; color: {current_color};">{energy} kWh</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if i == st.session_state.selected_route_index:
                    st.success("Selected")
                    if st.button("View Analysis", key=f"view_analysis_{i}", use_container_width=True, type="primary"):
                        st.session_state.dashboard_tab = "Analysis"
                        st.rerun()
                else:
                    if st.button("Select Route", key=f"select_route_{i}", use_container_width=True):
                        st.session_state.selected_route_index = i
                        st.session_state.dashboard_tab = "Analysis"
                        st.rerun()
                

def show_analysis(result):

    selected_route = get_selected_route(result)

    battery_left = selected_route.get("battery_left_percent", "N/A")
    energy_used = selected_route.get("total_energy_kwh", "N/A")
    distance = selected_route.get("total_distance_km", "N/A")
    weather = selected_route.get("weather_used", "N/A")
    input_battery = result.get("input_battery_percentage", "N/A")
    recommended_speed = selected_route.get("recommended_speed_kmh", "N/A")
    regen_saved = selected_route.get("regen_saved_kwh", 0)
    duration = selected_route.get("duration_min", "N/A")
    directions = selected_route.get("directions", [])
    route_points = selected_route.get("coordinates_3d", selected_route.get("3d_path", []))

    try:
        battery_used = round(float(input_battery) - float(battery_left), 1)
    except:
        battery_used = "N/A"

    st.markdown("## Route Analysis")

    # --- CHANGE 1: PREMIUM 4-COLUMN ROUTE HEADER CARDS ---
    source_val = result.get("source", "N/A").title()
    dest_val = result.get("destination", "N/A").title()
    vehicle_val = result.get("car_model", "EV")
    start_batt_val = result.get("input_battery_percentage", "N/A")

    hdr_c1, hdr_c2, hdr_c3, hdr_c4 = st.columns(4)

    with hdr_c1:
        st.markdown(f"""
            <div style="background: rgba(4, 18, 27, 0.75); border: 1px solid rgba(100, 255, 90, 0.2); border-radius: 12px; padding: 14px 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px;">
                <div style="font-size: 11px; color: #9ca3af; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">From</div>
                <div style="font-size: 22px; font-weight: 800; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{source_val}</div>
            </div>
        """, unsafe_allow_html=True)

    with hdr_c2:
        st.markdown(f"""
            <div style="background: rgba(4, 18, 27, 0.75); border: 1px solid rgba(100, 255, 90, 0.2); border-radius: 12px; padding: 14px 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px;">
                <div style="font-size: 11px; color: #9ca3af; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">To</div>
                <div style="font-size: 22px; font-weight: 800; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{dest_val}</div>
            </div>
        """, unsafe_allow_html=True)

    with hdr_c3:
        st.markdown(f"""
            <div style="background: rgba(4, 18, 27, 0.75); border: 1px solid rgba(100, 255, 90, 0.2); border-radius: 12px; padding: 14px 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px;">
                <div style="font-size: 11px; color: #9ca3af; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Vehicle</div>
                <div style="font-size: 22px; font-weight: 800; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{vehicle_val}</div>
            </div>
        """, unsafe_allow_html=True)

    with hdr_c4:
        st.markdown(f"""
            <div style="background: rgba(4, 18, 27, 0.75); border: 1px solid rgba(100, 255, 90, 0.2); border-radius: 12px; padding: 14px 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px;">
                <div style="font-size: 11px; color: #9ca3af; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Start Battery</div>
                <div style="font-size: 22px; font-weight: 800; color: #64ff5a;">{start_batt_val}%</div>
            </div>
        """, unsafe_allow_html=True)

    # --- MAIN ANALYSIS LAYOUT ---
    main_left, main_right = st.columns([1 , 1])

    with main_left:
        with st.container(border=True):
            st.caption("Predicted Battery at Arrival")
            st.markdown(
                f"""
                <div style="font-size:44px;font-weight:900;color:#ffffff;line-height:1;">
                    {battery_left}%
                </div>
                <div style="font-size:13px;color:#9ca3af;margin-top:4px;">
                    Battery used: {battery_used}%
                </div>
                """,
                unsafe_allow_html=True
            )

            try:
                st.progress(float(battery_left) / 100)
            except:
                st.progress(0)

            st.success("Good for this trip!")

    with main_right:
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            with st.container(border=True):
                 st.caption("Recommended Speed")
                 st.markdown(
                f"""
                <div style="font-size:42px;font-weight:900;color:#ffffff;line-height:1;">
                    {recommended_speed}
                    <span style="font-size:18px;color:#cbd5e1;">km/h</span>
                </div>
                <div style="font-size:13px;color:#9ca3af;margin-top:5px;">
                    Optimal for efficiency
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.container(border=True):
        
            # --- CHANGE 4: PREMIUM WEATHER BADGE ---
                 st.markdown(f"""
            <div style="margin-top: 18px; padding: 12px 16px; background: rgba(4, 18, 27, 0.6); border: 1px solid rgba(100, 255, 90, 0.25); border-radius: 10px; display: flex; align-items: center; gap: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size: 24px; line-height: 1;">🌦️</div>
                <div>
                    <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase; font-weight: 800; letter-spacing: 0.8px; margin-bottom: 3px;">Live Environmental Mesh</div>
                    <div style="font-size: 16px; font-weight: 900; color: #64ff5a; letter-spacing: 0.3px;">{weather}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with sub_c2:
            try:
                speed_val = float(recommended_speed)
            except:
                speed_val = 0.0
            gauge_degree = min((speed_val / 120.0) * 180, 180)
            st.markdown(f"""<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding-top: 10px;">
                <div style="position: relative; width: 160px; height: 80px; overflow: hidden;">
                    <div style="position: absolute; top: 0; left: 0; width: 160px; height: 160px; border-radius: 50%; border: 12px solid rgba(255, 255, 255, 0.05); box-sizing: border-box;"></div>
                    <div style="position: absolute; top: 0; left: 0; width: 160px; height: 160px; border-radius: 50%; border: 12px solid transparent; border-top-color: #22d45f; border-right-color: #22d45f; box-sizing: border-box; transform: rotate({-135 + (gauge_degree)}deg); transition: transform 0.5s ease;"></div>
                    <div style="position: absolute; bottom: 0; left: 50%; width: 14px; height: 14px; background: #ffffff; border-radius: 50%; transform: translate(-50%, 50%); z-index: 10;"></div>
                    <div style="position: absolute; bottom: 0; left: 50%; width: 4px; height: 65px; background: #ffffff; transform-origin: bottom center; transform: translate(-50%, 0) rotate({-90 + gauge_degree}deg); transition: transform 0.5s ease; border-radius: 2px; z-index: 5;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; width: 150px; margin-top: 4px; font-size: 10px; color: #6b7280; font-family: sans-serif; font-weight: 600;">
                    <span>0</span>
                    <span>60</span>
                    <span>120+</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    # main_left, mid_right = st.columns([0.95, 1.15])

    with main_left:
        with st.container(border=True):
            st.markdown("#### Battery Consumption Breakdown")
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>
                    <div style="color: #dce7ee; font-size: 15px; font-weight: 800;">Driving Energy</div>
                    <div style="color: #9ca3af; font-size: 12px; margin-top: 2px;">Total predicted mechanical consumption</div>
                </div>
                <div style="text-align: right; color: #ffffff; font-size: 24px; font-weight: 900; letter-spacing: 0.5px;">
                    {energy_used} <span style="font-size: 14px; color: #9ca3af; font-weight: 600;">kWh</span>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>
                    <div style="color: #dce7ee; font-size: 15px; font-weight: 800;">Regenerative Braking</div>
                    <div style="color: #9ca3af; font-size: 12px; margin-top: 2px;">Energy recovered while slowing down</div>
                </div>
                <div style="text-align: right; color: #22d45f; font-size: 24px; font-weight: 900; letter-spacing: 0.5px;">
                    -{regen_saved} <span style="font-size: 14px; color: #9ca3af; font-weight: 600;">kWh</span>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>
                    <div style="color: #dce7ee; font-size: 15px; font-weight: 800;">Weather Engine</div>
                    <div style="color: #9ca3af; font-size: 12px; margin-top: 2px;">Ambient mesh conditions used</div>
                </div>
                <div style="text-align: right; color: #64ff5a; font-size: 15px; font-weight: 700;">
                    {weather}
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0;">
                <div>
                    <div style="color: #dce7ee; font-size: 15px; font-weight: 800;">Net Battery Drain</div>
                    <div style="color: #9ca3af; font-size: 12px; margin-top: 2px;">Start battery minus arrival battery</div>
                </div>
                <div style="text-align: right; color: #ffffff; font-size: 24px; font-weight: 900;">
                    {battery_used}<span style="font-size: 18px; color: #9ca3af;">%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with main_right:
        with st.container(border=True):
            st.markdown("#### Route Elevation Profile")

            elevation_rows = []

            for i, point in enumerate(route_points):
                if len(point) >= 3:
                    elevation_rows.append({
                        "point": i,
                        "elevation": point[2]
                    })

            if elevation_rows:
                elevation_df = pd.DataFrame(elevation_rows)
                chart=(alt.Chart(elevation_df)
                    .mark_area(
                        line={'color': '#64ff5a', 'width': 2}, # Bright neon green line on top
                        color=alt.Gradient(                    # Fades to a deep transparent green at the bottom
                            gradient='linear',
                            stops=[
                                alt.GradientStop(color='rgba(100, 255, 90, 0.4)', offset=0),
                                alt.GradientStop(color='rgba(100, 255, 90, 0.0)', offset=1)
                            ],
                            x1=1, y1=0, x2=1, y2=1
                        )
                    )
                    .encode(
                        x=alt.X('point:Q', title='Point', scale=alt.Scale(zero=False)),
                        y=alt.Y('elevation:Q', title='Elevation (m)', scale=alt.Scale(zero=False))
                    )
                    .properties(
                        height=280 
                    )
                )
                
                # Render the custom Altair chart
                st.altair_chart(chart, use_container_width=True)
                    
            else:
                st.info("Elevation data unavailable.")

            # --- CHANGE 3: AI TELEMETRY ROW ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### AI Environmental Telemetry")
    
    uvp_c1, uvp_c2 = st.columns(2)
    
    with uvp_c1:
        # Thermal Soak Memory Logic
        thermal_temp = selected_route.get("thermal_soak_cabin_temp", 24.0)
        hvac_spent = selected_route.get("hvac_spent_kwh", 0.0)
        
        is_hot = float(thermal_temp) > 30.0
        t_color = "#ff4b4b" if is_hot else "#22d45f"
        t_bg = "rgba(40, 10, 10, 0.6)" if is_hot else "rgba(4, 18, 27, 0.6)"
        t_glow = "rgba(255, 75, 75, 0.15)" if is_hot else "rgba(34, 212, 95, 0.15)"
        t_icon = "🔥 High Cabin Thermal Mass" if is_hot else "❄️ Optimal Thermal State"
        
        st.markdown(f"""
        <div style="background: {t_bg}; border: 1px solid {t_color}; border-radius: 12px; padding: 20px; box-shadow: 0 0 20px {t_glow}; height: 100%;">
            <div style="color: {t_color}; font-size: 13px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px;">Thermal Memory Model</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 12px; color: #9ca3af;">Est. Cabin Soak Temp</div>
                    <div style="font-size: 32px; font-weight: 900; color: #fff;">{thermal_temp}°C</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 12px; color: #9ca3af;">Initial HVAC Penalty</div>
                    <div style="font-size: 32px; font-weight: 900; color: #fff;">{hvac_spent} <span style="font-size:16px; color:#cbd5e1;">kWh</span></div>
                </div>
            </div>
            <div style="background: rgba(0,0,0,0.4); padding: 10px; border-radius: 6px; font-size: 13px; color: #dce7ee; border-left: 3px solid {t_color};">
                <b>Status:</b> {t_icon}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with uvp_c2:
        # Solar Vectoring Logic
        solar_metrics = selected_route.get("solar_vector_metrics", {})
        bearing = solar_metrics.get("car_bearing_degrees", "N/A")
        azimuth = solar_metrics.get("sun_azimuth_degrees", "N/A")
        elevation = solar_metrics.get("sun_elevation_degrees", "N/A")
        solar_status = solar_metrics.get("solar_incident_status", "Neutral Data")
        solar_overhead = selected_route.get("solar_hvac_overhead_kwh", 0.0)
        
        s_color = "#ff9800"
        st.markdown(f"""
        <div style="background: rgba(20, 15, 5, 0.6); border: 1px solid {s_color}; border-radius: 12px; padding: 20px; box-shadow: 0 0 20px rgba(255, 152, 0, 0.15); height: 100%;">
            <div style="color: {s_color}; font-size: 13px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px;">☀️ Solar Insolation Vectoring</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 11px; color: #9ca3af;">Car Heading</div>
                    <div style="font-size: 20px; font-weight: 800; color: #fff;">{bearing}°</div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #9ca3af;">Sun Azimuth</div>
                    <div style="font-size: 20px; font-weight: 800; color: #fff;">{azimuth}°</div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #9ca3af;">Sun Elevation</div>
                    <div style="font-size: 20px; font-weight: 800; color: #fff;">{elevation}°</div>
                </div>
            </div>
            <div style="background: rgba(0,0,0,0.4); padding: 10px; border-radius: 6px; font-size: 13px; color: #dce7ee; border-left: 3px solid {s_color}; margin-bottom: 8px;">
                <b>Vector Alert:</b> {solar_status}
            </div>
            <div style="font-size: 12px; color: #9ca3af; text-align: right;">Dynamic GHG Penalty: <b style="color:#fff; font-size:14px;">+{solar_overhead} kWh</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- THREE-COLUMN SYMMETRICAL FOOTER SPLIT ---
    bot_left, bot_mid, bot_right = st.columns([1.2, 1, 1.1])
    
    with bot_left:
        with st.container(border=True):
            st.markdown("#### Turn-by-Turn Directions")
            if directions:
                for i, step in enumerate(directions[:7], start=1):
                    left, right = st.columns([5, 1])
                    left.write(f"**{i}.** {step.get('instruction', '')}")
                    right.caption(f"{step.get('distance_km', 'N/A')} km")
            else:
                st.info("Directions unavailable.")
    with bot_mid:
        with st.container(border=True):
            st.markdown("#### 🔌 Route Charging Hubs")

            stations_data = result.get("charging_hubs", [])

            if stations_data:
                for station in stations_data:
                   name = station.get("name", "Charging Station")
                   status = station.get("status", "N/A")
                   reliability = station.get("reliability_score", "N/A")
                   queue = station.get("queue_length", "N/A")
                   wait = station.get("estimated_wait_time_mins", "N/A")
                   message = station.get("status_message", "")

                   status_color = "#22d45f" if status == "Available" else "#ff9800"

                   st.markdown(f"""
                    <div style="background: rgba(4, 18, 27, 0.65); border: 1px solid rgba(100, 255, 90, 0.25); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);">
                        <div style="font-size: 15px; font-weight: 900; color: #ffffff;">{name}</div>
                        <div style="margin-top: 8px; font-size: 13px; color: #dce7ee;">Status: <span style="color: {status_color}; font-weight: 900;">{status}</span></div>
                        <div style="font-size: 13px; color: #9ca3af; margin-top: 4px;">Reliability: <b style="color:#ffffff;">{reliability}</b></div>
                        <div style="font-size: 13px; color: #9ca3af; margin-top: 4px;">Queue: <b style="color:#ffffff;">{queue}</b> &nbsp; | &nbsp; Wait: <b style="color:#ffffff;">{wait} mins</b></div>
                        <div style="margin-top: 8px; padding: 8px; border-radius: 6px; background: rgba(0,0,0,0.35); color: #dce7ee; font-size: 12px;">{message}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No charging hubs found for this route.")
                
                
    with bot_right:
        with st.container(border=True):
            st.markdown("#### Road Surface Breakdown")
            surface_summary = selected_route.get("surface_data", {}).get("summary", [])
            
            if surface_summary:
                surface_map = {
                    0: "Paved (Unknown)", 1: "Unpaved", 2: "Macadam", 3: "Asphalt", 
                    4: "Concrete", 5: "Cobblestone", 8: "Compacted", 10: "Gravel"
                }
                bar_colors = ["#1e90ff", "#9c27b0", "#22d45f", "#ff9800", "#e91e63"]
                
                list_html = "<ul style='color: #9ca3af; font-size: 13px; line-height: 2.2; list-style-type: none; padding-left: 0; margin-bottom: 0;'>"
                bar_html = "<div style='display: flex; width: 100%; height: 10px; border-radius: 6px; overflow: hidden; margin-top: 15px; box-shadow: 0 0 10px rgba(0,0,0,0.3);'>"
                
                for idx, item in enumerate(surface_summary):
                    val = item.get("value", 0)
                    dist_km = item.get("distance", 0) / 1000 
                    pct = item.get("amount", 0)
                    color = bar_colors[idx % len(bar_colors)]
                    surface_name = surface_map.get(val, f"Surface Type {val}")
                    
                    list_html += f"<li><span style='color:{color}; font-size:16px; margin-right:6px; vertical-align:middle;'>■</span> <b>{surface_name}</b>: {dist_km:.1f} km <span style='color:#64748b; font-size:11px;'>({pct:.1f}%)</span></li>"
                    bar_html += f"<div style='width: {pct}%; background-color: {color};' title='{surface_name}: {pct}%'></div>"
                    
                list_html += "</ul>"
                bar_html += "</div>"  # Closes the flex container wrapper
                
                # Render the legend and visual breakdown bar
                st.markdown(list_html, unsafe_allow_html=True)
                st.markdown(bar_html, unsafe_allow_html=True)
            else:
                st.info("Road surface profile data unavailable.")
def show_placeholder_page(title):
    st.title(title)
    st.info("This page can be developed later.")


def show_result_page():
    result = st.session_state.result

    show_sidebar(result)

    tab = st.session_state.dashboard_tab

    if tab == "Route Planner":
        show_route_planner(result)

    

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
            # ✅ CALLING FASTAPI ENGINE DIRECTLY NATIVELY
            result = asyncio.run(getdata(
                Source=source,
                Destination=destination,
                Car_Model=vehicle,
                Battery_percentage=int(battery)
            ))

            print(result)
            
            if result.get("status") == "failed":
                st.error(result.get("error", "An unknown error occurred."))
            else:
                routes = result.get("routes", [])
                selected_route = routes[0] if routes else {}

                st.session_state.result = result
                st.session_state.page = "result"
                st.session_state.dashboard_tab = "Route Planner"
                st.rerun()

        except Exception as e:
            st.error("Error executing simulation logic natively.")
            st.write(e)