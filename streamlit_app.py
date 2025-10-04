import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="🌾 Smart AgriTwin Dashboard", page_icon="🌱", layout="wide")

# LIGHT background for the whole app
st.markdown("""
<style>
.stApp { background-color: #f7f7eb; color: #151716; }
body, .stMarkdown, .stHeader, .stSubheader, .stCaption, .stTextInput > label, .stSelectbox > label, .stTextArea > label, .stTabs { color: #151716 !important;}
</style>
""", unsafe_allow_html=True)

# ------------------- HOME/LOGIN PAGE -------------------
def login_page():
    st.markdown("<h1 style='color:#40631e;text-align:center'>🌾 SMART AGRI TWIN</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#2e8b57;'>Optimizing Crop Yield & Market Access for Indian Farmers</h3>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=800&q=80", use_column_width=True)
    st.markdown(
        """
        <div style='background:rgba(255,255,255,0.85);padding:16px;border-radius:10px;'>
        <b>This project helps Indian farmers and agri-experts maximize crop yield & profit while reducing losses. Analyze your local soil and crops, and get actionable recommendations!</b>
        </div>
        """, unsafe_allow_html=True)
    with st.form("login"):
        name = st.text_input("Your Name")
        role = st.selectbox("Who are you?", ["Farmer", "Student", "Researcher", "Other"])
        purpose = st.text_area("Purpose for using the dashboard")
        submitted = st.form_submit_button("Enter Dashboard")
    if submitted and name:
        st.session_state.update({"auth": True, "name": name, "role": role, "purpose": purpose})

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login_page()
    st.stop()
else:
    # ------------------- LOAD DATA & CLEAN -------------------
    @st.cache_data
    def load():
        crop = pd.read_csv('icrisat_long_cleaned.csv')
        soil = pd.read_csv('Soil-data-cleaned.csv')
        return crop, soil
    crop, soil = load()

    crop.columns = crop.columns.str.strip()
    soil.columns = soil.columns.str.strip()
    if "District" in crop.columns and "District" in soil.columns:
        crop["District"] = crop["District"].astype(str).str.strip().str.title()
        soil["District"] = soil["District"].astype(str).str.strip().str.title()

    # ------------------- GREETING & PURPOSE -------------------
    st.success(f"Hello, {st.session_state['name']} ({st.session_state['role']})! Purpose: {st.session_state['purpose']}")
    st.write("---")
    st.markdown("**Use this dashboard to select crops, analyze your district's soil, and access vital agricultural guidance.**")

    # ------------------- DISTRICT SELECTION -------------------
    # Hardcoded district list from Soil-data.csv
districts = [
    "Yadgir",
    "Virudhunagar",
    "Villupuram",
    "Vijayapura",
    "Vijayanagar",
    "Vellore",
    "Valsad",
    "Vadodara",
    "Uttara Kannada",
    "Udupi",
    "Tuticorin",
    "Tumakuru",
    "Tiruvannamalai",
    "Tiruppur",
    "Tirupathur",
    "Tirunelveli"
]

selected_district = st.selectbox("Select a District to View Recommendations", districts)

    # ------------------- KEY RECOMMENDATION -------------------
    st.header("🌿 Crop Recommendations by District (by Soil Nitrogen)")
    try:
        crop_row = crop[crop['District'] == selected_district]
        soil_row = soil[soil['District'] == selected_district]

        if not crop_row.empty and not soil_row.empty:
            merged = pd.merge(crop_row, soil_row, on="District")

            # Select the crop with maximum Nitrogen value as recommended (example strategy)
            best_crop_row = merged.loc[merged['Nitrogen'].idxmax()]
            st.table(pd.DataFrame({
                'District': [selected_district],
                'Recommended Crop': [best_crop_row['Crop']],
                'Avg. Soil N': [round(best_crop_row['Nitrogen'], 2)]
            }))
            st.markdown("> _Prioritize crop choice in high-nitrogen districts. Consider interventions for low-nitrogen/low-yield districts._")
        else:
            st.warning("No data available for this district!")
    except Exception as e:
        st.error(f"Error fetching recommendation: {e}")

    # ------------------- VISUALIZATION TABS -------------------
    tabs = st.tabs([
        "Wheat by District", "Wheat Over Years",
        "Main Crop by District", "Average Soil pH",
        "Soil Nitrogen Distribution", "Soil Correlation"
    ])

    with tabs[0]:
        st.subheader("🌾 Total Wheat Production by District")
        if "Crop" in crop.columns and "District" in crop.columns and "Production" in crop.columns:
            wheat = crop[crop["Crop"].str.lower() == "wheat"]
            dist_data = wheat.groupby('District')['Production'].sum().reset_index()
            fig = px.bar(dist_data, x='District', y='Production', color='Production', color_continuous_scale='YlGn', title="Wheat Production by District")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Some districts excel at wheat—share their soil/market strategies!")

    with tabs[1]:
        st.subheader("🌱 Wheat Production Over Years")
        if "Year" in crop.columns and "Production" in crop.columns:
            prod_year = wheat.groupby('Year')['Production'].sum().reset_index()
            fig = px.line(prod_year, x='Year', y='Production', color_discrete_sequence=["#27ae60"], title="Wheat Production Trend")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Yearly trends show crop changes, technology impact, climate effects.")

    with tabs[2]:
        st.subheader("🌽 Main Crop Production by District")
        if "Crop" in crop.columns and "District" in crop.columns and "Production" in crop.columns:
            main_crops = crop.groupby(['District', 'Crop'])['Production'].sum().reset_index()
            fig = px.bar(main_crops, x='District', y='Production', color='Crop', barmode='group', title="Wheat vs Maize Production by District", color_discrete_sequence=px.colors.qualitative.G10)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Direct comparison helps allocation and crop rotation planning.")

    with tabs[3]:
        st.subheader("🧪 Average Soil pH by District")
        if "District" in soil.columns and "pH" in soil.columns:
            avg_ph = soil.groupby('District')['pH'].mean().sort_values().reset_index()
            fig = px.bar(avg_ph, x='District', y='pH', color='pH', color_continuous_scale='Sunset', title="Average Soil pH by District")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Optimal soil pH districts correlate with higher yields.")

    with tabs[4]:
        st.subheader("🌱 Distribution of Soil Nitrogen")
        if "Nitrogen" in soil.columns:
            fig = px.histogram(soil, x='Nitrogen', nbins=20, color_discrete_sequence=["#449966"], title="Soil Nitrogen Histogram")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Low-nitrogen regions may need fertilizer intervention.")

    with tabs[5]:
        st.subheader("🧬 Correlation of Soil Features")
        num_cols = soil.select_dtypes(include='number')
        fig = px.imshow(num_cols.corr(), color_continuous_scale='YlOrBr', title="Soil Feature Correlation Heatmap", aspect='auto')
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Correlations reveal key drivers of crop outcomes.")

    # ------------------- SUMMARY -------------------
    st.header("Recommendations & Best Practices")
    st.markdown("- Replicate best practices of high-yield districts in lower-yield areas.")
    st.markdown("- Apply lime and fertilizer to balance soil pH and nitrogen.")
    st.markdown("- Use soil maps to target crop choices for each location.")
    st.markdown("- Support ongoing research and technology deployment for sustainable gains.")
    st.image("https://cdn.pixabay.com/photo/2015/09/09/19/34/agriculture-933167_1280.jpg", caption="Indian Farmers — The Heart of Our Nation", use_column_width=True)
