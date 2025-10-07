import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Smart AgriTwin Dashboard", page_icon="🌾", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f9f9e3; }
</style>
""", unsafe_allow_html=True)

def home():
    st.markdown("<h1 style='text-align:center; color:#67a167;'>🌾 SMART AGRI TWIN</h1>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=800&q=80", use_column_width=True)
    st.markdown("<div style='background:rgba(255,255,255,0.85);padding:16px;border-radius:10px;'><b>This dashboard helps Indian farmers, students, and researchers find the best crop choices and market opportunities using real field data.</b></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        name = st.text_input("Your Name")
        role = st.selectbox("Who are you?", ["Farmer","Student","Researcher","Other"])
        purpose = st.text_area("Purpose for entering dashboard")
        submit = st.form_submit_button("Enter Dashboard")
    if submit and name:
        st.session_state.auth = True
        st.session_state.user = {"name": name, "role": role, "purpose": purpose}

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    home()
    st.stop()

user = st.session_state.user
st.success(f"Hello, {user['name']} ({user['role']})! Purpose: {user['purpose']}")
st.write("---")

@st.cache_data
def load_data():
    crop = pd.read_csv('icrisat_long_cleaned.csv')
    soil = pd.read_csv('Soil-data-cleaned.csv')
    try:
        timeseries = pd.read_csv('fields_timeseries.csv', parse_dates=['date'])
    except:
        data = {
            "date": pd.date_range(start='2020-04-02', end='2020-10-25').repeat(3),
            "location": ["Field_A"]*207 + ["Field_B"]*207 + ["Field_C"]*207,
            "soil_moisture": [25 + 5 * i%5 for i in range(621)],
            "yield_t_ha": [5 + 0.5 * i%7 for i in range(621)]
        }
        timeseries = pd.DataFrame(data)
    return crop, soil, timeseries

crop, soil, timeseries = load_data()

for df in (crop, soil):
    df.columns = df.columns.str.strip()
    if "District" in df.columns:
        df["District"] = df["District"].astype(str).str.strip().str.title()

field_coords = {
    'Field_A': {'lat': 11.01, 'lon': 77.03},
    'Field_B': {'lat': 11.02, 'lon': 77.04},
    'Field_C': {'lat': 11.03, 'lon': 77.05},
}

if 'lat' not in timeseries.columns or 'lon' not in timeseries.columns:
    timeseries['lat'] = timeseries['location'].map(lambda x: field_coords.get(x, {}).get('lat', None))
    timeseries['lon'] = timeseries['location'].map(lambda x: field_coords.get(x, {}).get('lon', None))

# Show number of fields and list them
field_list = timeseries['location'].unique()
num_fields = len(field_list)
st.info(f"Number of unique fields in dataset: {num_fields}  — Fields: {', '.join(field_list)}")

# Slicers for date and fields
col1, col2 = st.columns(2)
with col1:
    date_range = st.date_input("Date Range", [timeseries['date'].min().date(), timeseries['date'].max().date()])
with col2:
    locations = st.multiselect("Fields", field_list, default=list(field_list))

filtered = timeseries[
    (timeseries['date'] >= pd.to_datetime(date_range[0])) &
    (timeseries['date'] <= pd.to_datetime(date_range[1])) &
    (timeseries['location'].isin(locations))
]

# KPIs in one row
k1, k2, k3 = st.columns(3)
avg_sm = filtered['soil_moisture'].mean() if not filtered.empty else 0
avg_yield = filtered['yield_t_ha'].mean() if not filtered.empty else 0
fields_need_irrig = filtered[filtered['soil_moisture'] < 20]['location'].nunique() if not filtered.empty else 0
k1.metric("Avg Soil Moisture (7-day)", f"{avg_sm:.2f}")
k2.metric("Avg Yield (t/ha)", f"{avg_yield:.2f}")
k3.metric("Fields needing irrigation (today)", fields_need_irrig)

st.write("---")

# Timeseries soil moisture plot
st.subheader("Daily Soil Moisture by Field")
if not filtered.empty:
    fig = px.line(filtered, x='date', y='soil_moisture', color='location', labels={'soil_moisture':'Soil Moisture'})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for chosen filter.")

# Geographic map of soil moisture
st.subheader("Average Soil Moisture by Field")
if not filtered.empty and filtered[['lat','lon']].notna().any().any():
    map_data = filtered.groupby('location').agg({'lat':'first','lon':'first','soil_moisture':'mean'}).reset_index()
    map_fig = px.scatter_mapbox(
        map_data, lat='lat', lon='lon', color='location', size='soil_moisture',
        hover_name='location', zoom=7, height=350, mapbox_style='open-street-map'
    )
    st.plotly_chart(map_fig, use_container_width=True)
else:
    st.info("No location map data for current filters.")

# Average yield by location bar chart
st.subheader("Average Yield by Location (t/ha)")
if not filtered.empty:
    yield_data = filtered.groupby('location')['yield_t_ha'].mean().reset_index()
    yield_fig = px.bar(yield_data, y='location', x='yield_t_ha', orientation='h')
    st.plotly_chart(yield_fig, use_container_width=True)
else:
    st.info("No yield data for current filter.")

# Original district level tabs below

tabs = st.tabs([
    "Wheat by District", "Wheat Over Years",
    "Main Crop by District", "Average Soil pH",
    "Soil Nitrogen", "Soil Correlation"
])

with tabs[0]:
    st.subheader("🌾 Total Wheat Production by District")
    wheat = crop[crop["Crop"].str.lower() == "wheat"]
    dist_data = wheat.groupby('District')['Production'].sum().reset_index()
    fig = px.bar(dist_data, x='District', y='Production', color='Production', color_continuous_scale='YlGn')
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("🌱 Wheat Production Over Years")
    prod_year = wheat.groupby('Year')['Production'].sum().reset_index()
    fig = px.line(prod_year, x='Year', y='Production', color_discrete_sequence=["#67a167"])
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("🌽 Main Crop Production by District")
    main_crops = crop.groupby(['District', 'Crop'])['Production'].sum().reset_index()
    fig = px.bar(main_crops, x='District', y='Production', color='Crop', barmode='group', color_discrete_sequence=px.colors.qualitative.G10)
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("🧪 Average Soil pH by District")
    avg_ph = soil.groupby('District')['pH'].mean().sort_values().reset_index()
    fig = px.bar(avg_ph, x='District', y='pH', color='pH', color_continuous_scale='Sunset')
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader("🌱 Soil Nitrogen Distribution")
    fig = px.histogram(soil, x='Nitrogen', nbins=20, color_discrete_sequence=["#449966"])
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader("🧬 Soil Feature Correlation")
    num_cols = soil.select_dtypes(include='number')
    fig = px.imshow(num_cols.corr(), color_continuous_scale='YlOrBr')
    st.plotly_chart(fig, use_container_width=True)

# Crop recommendations table

st.header("🌿 Crop Recommendations by District")
try:
    merged = pd.merge(crop, soil, on="District")
    top_crops = merged.groupby(['District','Crop'])['Nitrogen'].mean().reset_index()
    best = top_crops.sort_values('Nitrogen', ascending=False).groupby('District').first().reset_index()
    st.table(best.rename(columns={"Crop":"Recommended Crop","Nitrogen":"Avg. Soil N"}))
    st.markdown("> _Focus on high-nitrogen districts for best crop yield; intervene in soils with poor nitrogen._")
except Exception as e:
    st.error(f"Error merging: {e}")

# Recommendations section
st.header("Recommendations & Best Practices")
st.write("- Learn from high-yield districts.")
st.write("- Apply soil amendments and fertilizer as needed.")
st.write("- Make decisions based on real farm & soil data.")
st.image("https://cdn.pixabay.com/photo/2015/09/09/19/34/agriculture-933167_1280.jpg", caption="Indian Farmers: Wisdom and Growth", use_column_width=True)
