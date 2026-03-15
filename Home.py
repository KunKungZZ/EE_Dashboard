import streamlit as st
import pulp as pl
import plotly.graph_objects as go
import altair as alt
import pandas as pd
import json
import os

FILENAME = 'appliance_data.json'
# Page config
st.set_page_config(
    page_title="Home Energy Management System",
    layout="wide"
)
# Title
st.title("Home Energy Management System Dashboard")
st.markdown("Optimize your home energy consumption with solar and battery storage")

def load_data():
    if not os.path.exists(FILENAME):
        st.error(f"Don't found JSON file: {FILENAME}")
        return None
    with open(FILENAME, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(FILENAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    st.success(f"Success to save {FILENAME} file")

def add_appliance(name, power, time_list):
    data = load_data()
    if data is None: 
        return False

    if name in data["load_power"]:
        st.warning(f"Have '{name}' in Load Devices")
        return False

    data["load_power"][name] = power
    data["load_work_time"][name] = time_list
    
    save_data(data)
    st.success(f"Added: {name} in Load Devices")
    return True

def update_appliance(name, new_power=None, new_time_list=None):
    data = load_data()
    if data is None: 
        return False

    if name not in data["load_power"]:
        st.error(f"Error: don't found '{name}' in Load Devices")
        return False

    if new_power is not None:
        old_power = data["load_power"][name]
        data["load_power"][name] = new_power
        st.info(f"Updated {name} Power: {old_power} -> {new_power}")

    if new_time_list is not None:
        old_time = data["load_work_time"][name]
        data["load_work_time"][name] = new_time_list
        st.info(f"Updated {name} Time: {old_time} -> {new_time_list}")

    save_data(data)
    return True

def delete_appliance(name):
    data = load_data()
    if data is None: 
        return False

    if name in data["load_power"]:
        del data["load_power"][name]
        
        if name in data["load_work_time"]:
            del data["load_work_time"][name]
            
        save_data(data)
        st.success(f"Deleted: {name} from Load Devices")
        return True
    else:
        st.error(f"Error: '{name}' don't found in Load Devices")
        return False

# ==========================================
# LOAD DATA FROM JSON
# ==========================================

@st.cache_data
def load_appliance_data():
    data = load_data()
    if data is None:
        return st.error("Uplord applicane data to server")
    return data

# Load data
appliance_data = load_appliance_data()
load_power = appliance_data["load_power"]
load_work_time = appliance_data["load_work_time"]

@st.dialog("Appliance Management")
def recheck_add(name):
    st.badge(f"{name}", color="red")
    st.write(f"Add {name} in Load Devices?")
    if st.button("Add Appliance",use_container_width=True,type="primary"):
        if add_appliance(new_name, new_power, [new_start, new_end, new_duration]):
                    st.cache_data.clear()
                    st.rerun()
@st.dialog("Appliance Management")
def recheck_update(name):
    st.badge(f"{name}", color="red")
    st.write(f"Update {name} profile?")
    if st.button("Update Device",use_container_width=True,type="primary"):
            if update_appliance(update_device, update_power, [update_start, update_end, update_duration]):
                st.cache_data.clear()
                st.rerun()
@st.dialog("Appliance Management")
def recheck_delete(name):
    st.badge(f"{name}", color="red")
    st.write(f"Delete {name} from Load Devices?")
    if st.button("Delete Device",use_container_width=True,type="primary"):
            if delete_appliance(delete_device):
                st.cache_data.clear()
                st.rerun()

# SIDEBAR - CONFIGURATION
# ==========================================
st.sidebar.header("⚙️ System Configuration")
st.sidebar.subheader("🔧 Devices Management")
with st.sidebar.expander("Manage Devices"):
    management_action = st.radio("Action", ["Add", "Update", "Delete"])
    
    if management_action == "Add":
        new_name = st.text_input("Device Name")
        new_power = st.number_input("Power (kW)", min_value=0.01, max_value=10.0, value=1.0, step=0.1)
        new_start = st.number_input("Start Hour", min_value=0, max_value=23, value=0)
        new_end = st.number_input("End Hour", min_value=1, max_value=24, value=24)
        new_duration = st.number_input("Duration (hours)", min_value=1, max_value=24, value=1)
        
        if st.button("Add Device",use_container_width=True,type="primary"):
            if new_name:
                recheck_add(new_name)
            else:
                st.error("Please enter device name")
    
    elif management_action == "Update":
        update_device = st.selectbox("Select Device", list(load_power.keys()))
        update_power = st.number_input("New Power (kW)", min_value=0.01, max_value=10.0, 
                                       value=load_power[update_device], step=0.1)
        current_time = load_work_time[update_device]
        update_start = st.number_input("Start Hour", min_value=0, max_value=23, value=current_time[0])
        update_end = st.number_input("End Hour", min_value=1, max_value=24, value=current_time[1])
        update_duration = st.number_input("Duration (hours)", min_value=1, max_value=24, value=current_time[2])
        
        if st.button("Update Device",use_container_width=True,type="primary"):
            recheck_update(update_device)
    
    elif management_action == "Delete":
        delete_device = st.selectbox("Select Device to Delete", list(load_power.keys()))
        if st.button("Delete Device",use_container_width=True,type="primary"):
            recheck_delete(delete_device)

# Solar configuration
st.sidebar.subheader("☀️ Solar System")
use_solar = st.sidebar.toggle("Enable Solar Generation", value=True)

# Battery configuration
if use_solar:
    st.sidebar.subheader("🔋 Battery Storage")
    use_battery = st.sidebar.toggle("Enable Battery Storage", value=True)

    if use_battery:
        bat_capacity = st.sidebar.slider("Battery Capacity (kWh)", 5.0, 20.0, 10.0, 0.5)
        bat_eff = st.sidebar.slider("Battery Efficiency (%)", 80, 100, 95) / 100
        soc_min_pct = st.sidebar.slider("Minimum SOC (%)", 10, 30, 20)
        soc_max_pct = st.sidebar.slider("Maximum SOC (%)", 70, 100, 90)
        soc_initial = st.sidebar.slider("Initial SOC (kWh)", 0.0, bat_capacity, 2.0, 0.5)
    else:
        bat_capacity = 10.0
        bat_eff = 0.95
        soc_min_pct = 20
        soc_max_pct = 90
        soc_initial = 20

    soc_min = (soc_min_pct / 100) * bat_capacity
    soc_max = (soc_max_pct / 100) * bat_capacity
else:
    use_battery = False
# Run optimization button
if st.sidebar.button("Run Optimization", type="primary",use_container_width=True):
    st.session_state.run_optimization = True

# Initialize session state
if 'run_optimization' not in st.session_state:
    st.session_state.run_optimization = False

# CONSTANTS FROM TEST1.PY
# ==========================================

hours = range(24)
price = [5.7982 if 9 <= h < 23 else 2.6369 for h in hours]  # TOU
solar_gen = [0, 0, 0, 0, 0, 0, 0.2, 0.8, 1.5, 2.5, 3.5, 4.5, 5.0, 4.8, 3.8, 2.5, 1.2, 0.3, 0, 0, 0, 0, 0, 0]


# DISPLAY INITIAL INFORMATION
# ==========================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Devices", len(load_power),border=True)
    
with col2:
    if use_solar:
        st.metric("Solar Generation", f"{sum(solar_gen)} kW",border=True)
    else:
        st.metric("Solar Generation", "Disabled",border=True)
        
with col3:
    if use_battery:
        st.metric("Battery Capacity", f"{bat_capacity} kWh",border=True)
    else:
        st.metric("Battery Capacity", "Disabled",border=True)

# Show price profile
st.subheader("Electricity Price Profile")
df = pd.DataFrame({
        "Price(฿/kWh)": price,
        "Hour" : hours})
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Hour"], y=df["Price(฿/kWh)"],name="Price(฿/kWh)", line_shape='hv',line=dict(color='#FF4B4B',width = 3)))
fig.update_layout(xaxis_title="Hour",yaxis_title="Price (฿)")
st.plotly_chart(fig, use_container_width=True)

# RUN OPTIMIZATION (BACKEND FROM TEST1.PY)
# ==========================================

if st.session_state.run_optimization:
    with st.spinner("Running optimization..."):
        # Create optimization model (same as TEST1.py)
        model = pl.LpProblem("HEMS_12Loads", pl.LpMinimize)
        x = {dev: pl.LpVariable.dicts(dev, hours, cat="Binary") for dev in load_power.keys()}
        grid_buy = pl.LpVariable.dicts("grid_buy", hours, lowBound=0)
        
        if use_battery:
            p_ch = pl.LpVariable.dicts("p_ch", hours, lowBound=0)
            p_dis = pl.LpVariable.dicts("p_dis", hours, lowBound=0)
            soc = pl.LpVariable.dicts("soc", hours, lowBound=soc_min, upBound=soc_max)
        
        # Objective: Minimize Total Cost
        model += pl.lpSum(grid_buy[h] * price[h] for h in hours)
        
        # Constraints (same as TEST1.py)
        for h in hours:
            total_load_h = pl.lpSum(load_power[dev] * x[dev][h] for dev in load_power.keys())
            model += total_load_h <= 5
            
            if use_solar and not use_battery:
                current_solar = solar_gen[h] if use_solar else 0
                model += grid_buy[h] >= total_load_h - current_solar
            elif not use_solar and not use_battery:
                model += grid_buy[h] >= total_load_h
            
            if use_solar and use_battery:
                # Energy Balance: Buy = Load + Charge - Solar - Discharge
                model += grid_buy[h] >= total_load_h + p_ch[h] - solar_gen[h] - p_dis[h]

                # Battery SOC Logic
                if h == 0:
                    model += soc[h] == soc_initial + (p_ch[h] * bat_eff) - (p_dis[h] / bat_eff)
                else:
                    model += soc[h] == soc[h-1] + (p_ch[h] * bat_eff) - (p_dis[h] / bat_eff)
        
        # Time Window Constraints
        for dev in load_power.keys():
            start, end, duration = load_work_time[dev]
            model += pl.lpSum(x[dev][h] for h in range(start, end)) == duration
        
        # Solve
        model.solve(pl.PULP_CBC_CMD(msg=0))
        
        # Extract results (same as TEST1.py)
        res_load = [sum(load_power[dev] * pl.value(x[dev][h]) for dev in load_power.keys()) for h in hours]
        res_grid_buy = [pl.value(grid_buy[h]) for h in hours]
        
        if use_battery:
            res_soc = [pl.value(soc[h]) for h in hours]
            res_p_ch = [pl.value(p_ch[h]) for h in hours]
            res_p_dis = [pl.value(p_dis[h]) for h in hours]
        
        schedule = {}
        for dev in load_power.keys():
            schedule[dev] = [h for h in hours if pl.value(x[dev][h]) == 1]
        
        # Display results
        
        # Key metrics
        total_cost = pl.value(model.objective)
        total_load = sum(res_load)
        total_grid = sum(res_grid_buy)
        st.subheader("Registered Devices")
    
        device_data = []
        for dev in load_power.keys():
            start, end, duration = load_work_time[dev]
            device_data.append({
                "Device": dev,
                "Power (kW)": load_power[dev],
                "Time Window": f"{start:02d}:00 - {end:02d}:00",
                "Required Hours": duration
            })
    
        df_devices = pd.DataFrame(device_data)
        st.dataframe(df_devices, use_container_width=True)

        st.success(f"✅ Optimization Status: {pl.LpStatus[model.status]}")
        st.subheader("Energy Management Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Daily Cost", f"฿{total_cost:.2f}",border=True)
        
        with col2:
            st.metric("Total Load", f"{total_load:.2f} kWh",border=True)
        
        with col3:
            st.metric("Grid Import", f"{total_grid:.2f} kWh",border=True)
        
        with col4:
            if use_solar:
                total_solar = sum(solar_gen)
                if total_solar > 0:
                    solar_used = min(total_solar, total_load)
                    st.metric("Solar Utilization", f"{(solar_used/total_solar*100):.1f}%",border=True)
                else:
                    st.metric("Solar Utilization", "0%",border=True)
        
        #virsulization
        df_plot = pd.DataFrame({
            "Hour": hours,
            "Price(฿/kWh)": price,
            "Total Load(kW)": res_load,
            "Grid Buy(kW)": res_grid_buy,
        })
        if use_solar:
            df_plot["Solar Gen(kW)"] = solar_gen
        if use_battery:
            df_plot["Charge(kW)"] = res_p_ch
            df_plot["Discharge(kW)"] = [-v for v in res_p_dis]
            df_plot["SOC(kWh)"] = res_soc
        fig = go.Figure()
        if not use_solar and not use_battery:
            options = st.multiselect("Filter of parameter",
            ["Price(฿/kWh)", "Total Load(kW)", "Grid Buy(kW)"],
            default=["Price(฿/kWh)", "Total Load(kW)", "Grid Buy(kW)"])
        elif use_solar and not use_battery:
            options = st.multiselect("Filter of parameter",
            ["Price(฿/kWh)", "Total Load(kW)", "Grid Buy(kW)", "Solar Gen(kW)"],
            default=["Price(฿/kWh)", "Total Load(kW)", "Grid Buy(kW)", "Solar Gen(kW)"])
        elif use_solar and use_battery:
            options = st.multiselect("Filter of parameter",
            ["Price(฿/kWh)", "Total Load(kW)", "Grid Buy(kW)", "Solar Gen(kW)","Charge(kW)","Discharge(kW)","SOC(kWh)"],
            default=["Price(฿/kWh)", "Total Load(kW)", "Grid Buy(kW)", "Solar Gen(kW)","Charge(kW)","Discharge(kW)","SOC(kWh)"])
        if "Price(฿/kWh)" in options:
            fig.add_trace(go.Scatter(x=df_plot["Hour"], y=df_plot["Price(฿/kWh)"],name="Price(฿/kWh)", line_shape='hv',line=dict(color='#FF4B4B', dash='dash', width=2)))
        if "Total Load(kW)" in options:
            fig.add_trace(go.Bar(x=df_plot["Hour"], y=df_plot["Total Load(kW)"],name="Total Load(kW)", marker_color='gray'))
        if "Grid Buy(kW)" in options:
            fig.add_trace(go.Bar(x=df_plot["Hour"], y=df_plot["Grid Buy(kW)"], name="Grid Buy(kW)", marker_color='darkviolet'))    
        if use_solar and "Solar Gen(kW)" in options:
            fig.add_trace(go.Scatter(x=df_plot["Hour"], y=df_plot["Solar Gen(kW)"],name="Solar Gen(kW)", mode='lines+markers',line=dict(color='orange', width=3)))
        if use_battery:
            if "Charge(kW)" in options:
                fig.add_trace(go.Bar(x=df_plot["Hour"], y=df_plot["Charge(kW)"], name="Charge(kW)", marker_color='blue', opacity=0.6))
            if "Discharge(kW)" in options:
                fig.add_trace(go.Bar(x=df_plot["Hour"], y=df_plot["Discharge(kW)"], name="Discharge(kW)", marker_color='lime', opacity=0.6))
            if "SOC(kWh)" in options:
                fig.add_trace(go.Scatter(x=df_plot["Hour"], y=df_plot["SOC(kWh)"], name="SOC (kWh)", mode='lines+markers',line=dict(color='green', dash='dot')))
        
        title_text = "Home Energy Management System: Optimization Summary"
        if not use_solar and not use_battery: 
            title_text += " (No solar + No battery)"
        elif use_solar and not use_battery: 
            title_text += " (Solar + No battery)"
        else: 
            title_text += " (Solar + Battery)"
        fig.update_layout(
            title=title_text,
            xaxis_title="Hour of Day (0-23)",
            yaxis_title="Power (kW) / Energy (kWh) / Price (฿)",
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=80, b=20),
            hovermode="x unified", 
            height=600
        )
        fig.update_xaxes(range=[0, 24], dtick=1)
        st.plotly_chart(fig, use_container_width=True)
        
        data = []
        device_names = list(load_power.keys())
        for dev in device_names:
            active_h = sorted([h for h in hours if pl.value(x[dev][h]) > 0.5])
            if not active_h:
                continue
            if active_h:
                start_hour = active_h[0]
                for i in range(1, len(active_h)):
                    if active_h[i] != active_h[i-1] + 1:
                        data.append({"Appliance": dev,"Start": start_hour,"End": active_h[i-1] + 1})
                        start_hour = active_h[i]
                data.append({"Appliance": dev,"Start": start_hour,"End": active_h[-1] + 1})
        
        df_plot = pd.DataFrame(data)
        chart = alt.Chart(df_plot).mark_bar(color='#FF4B4B').encode(
            x=alt.X('Start:Q', title='Hour of Day (0-23)', scale=alt.Scale(domain=[0, 24])),x2='End:Q',
            y=alt.Y('Appliance:N', title=None, sort=None),
            tooltip=['Appliance', 'Start', 'End']
            ).properties(width=700,height=400,title="Appliance Operation Schedule"
            ).configure_axis(grid=True)
        st.altair_chart(chart, use_container_width=True)

        # Detailed schedule table
        st.subheader("Detailed Device Schedule")
        
        schedule_data = []
        for dev in load_power.keys():
            hours_active = schedule[dev]
            schedule_data.append({
                "Device": dev,
                "Power (kW)": load_power[dev],
                "Operating Hours": str(hours_active),
                "Total Hours": len(hours_active),
                "Energy (kWh)": load_power[dev] * len(hours_active)
            })
        
        df_schedule = pd.DataFrame(schedule_data)
        #st.dataframe(df_schedule,column_config={"Operating Hours": st.column_config.Column("Operating Hours",width="large")})
        st.dataframe(df_schedule,use_container_width=True)
        # Hourly breakdown
        st.subheader("Hourly Energy Breakdown")
        
        hourly_data = {
            "Hour": list(hours),
            "Load (kW)": res_load,
            "Grid Buy (kW)": res_grid_buy,
            "Price (฿/kWh)": price,
            "Cost (฿)": [res_grid_buy[h] * price[h] for h in hours]
        }
        
        if use_solar:
            hourly_data["Solar (kW)"] = solar_gen
        
        if use_battery:
            hourly_data["Charge (kW)"] = res_p_ch
            hourly_data["Discharge (kW)"] = res_p_dis
            hourly_data["SOC (kWh)"] = res_soc
        
        df_hourly = pd.DataFrame(hourly_data)
        st.dataframe(df_hourly, use_container_width=True)

else:
    # Show device information
    st.subheader("Registered Devices")
    
    device_data = []
    for dev in load_power.keys():
        start, end, duration = load_work_time[dev]
        device_data.append({
            "Device": dev,
            "Power (kW)": load_power[dev],
            "Time Window": f"{start:02d}:00 - {end:02d}:00",
            "Required Hours": duration
        })
    
    df_devices = pd.DataFrame(device_data)
    st.dataframe(df_devices, use_container_width=True)
    st.info("Configure your system settings in the sidebar and click 'Run Optimization' to see results")
