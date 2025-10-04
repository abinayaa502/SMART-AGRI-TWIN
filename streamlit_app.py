import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Smart AgriTwin Dashboard", page_icon="🌾", layout="wide")

# Light background
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
    return crop, soil

crop, soil = load_data()
for df in (crop, soil):
    df.columns = df.columns.str.strip()
    if "District" in df.columns:
        df["District"] = df["District"].astype(str).str.strip().str.title()

# Recommendations
st.header("🌿 Crop Recommendations by District")
try:
    merged = pd.merge(crop, soil, on="District")
    top_crops = merged.groupby(['District','Crop'])['Nitrogen'].mean().reset_index()
    best = top_crops.sort_values('Nitrogen', ascending=False).groupby('District').first().reset_index()
    st.table(best.rename(columns={"Crop":"Recommended Crop","Nitrogen":"Avg. Soil N"}))
    st.markdown("> _Focus on high-nitrogen districts for best crop yield; intervene in soils with poor nitrogen._")
except Exception as e:
    st.error(f"Error merging: {e}")

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

st.header("Recommendations & Best Practices")
st.write("- Learn from high-yield districts.")
st.write("- Apply soil amendments and fertilizer as needed.")
st.write("- Make decisions based on real farm & soil data.")
st.image("https://cdn.pixabay.com/photo/2015/09/09/19/34/agriculture-933167_1280.jpg", caption="Indian Farmers: Wisdom and Growth", use_column_width=True)
