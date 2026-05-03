import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime

# --- CONFIG ---
USDA_API_KEY = st.secrets["O7FEwaRepBGrFWVnyosufLD3EmZKavzh29i3A7Cr"]

st.set_page_config(page_title="Free NutriTracker", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
today_str = datetime.now().strftime("%Y-%m-%d")

# --- APP UI ---
st.title("🥗 Lifetime Free Indian NutriLog")
st.info("Using USDA Open Data - No Monthly Fees")

# --- SECTION 1: SEARCH ---
query = st.text_input("Search for an ingredient (e.g., 'Lentils', 'Basmati', 'Chicken')", "")

if query:
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}&query={query}&pageSize=5"
    res = requests.get(url).json()
    
    if "foods" in res and len(res["foods"]) > 0:
        options = {f"{f['description']} ({f.get('brandOwner', 'Generic')})": f for f in res["foods"]}
        selected_food_name = st.selectbox("Select the closest match:", options.keys())
        selected_food = options[selected_food_name]
        
        grams = st.number_input("Amount in grams:", min_value=1, value=100)
        
        if st.button("Log this Food"):
            # Extracting nutrients from USDA format
            nutrients = {n['nutrientName']: n['value'] for n in selected_food['foodNutrients']}
            
            # USDA provides data per 100g. We scale it.
            factor = grams / 100.0
            
            entry = {
                "Date": today_str,
                "Time": datetime.now().strftime("%H:%M"),
                "Food": selected_food_name,
                "Grams": grams,
                "Calories": nutrients.get("Energy", 0) * factor,
                "Protein": nutrients.get("Protein", 0) * factor,
                "Carbs": nutrients.get("Carbohydrate, by difference", 0) * factor,
                "Fat": nutrients.get("Total lipid (fat)", 0) * factor,
                "Iron_mg": nutrients.get("Iron, Fe", 0) * factor,
                "Sodium_mg": nutrients.get("Sodium, Na", 0) * factor
            }
            
            # Save to Google Sheets
            existing_food = conn.read(worksheet="Sheet1", ttl=0)
            conn.update(worksheet="Sheet1", data=pd.concat([existing_food, pd.DataFrame([entry])]))
            st.success(f"Logged {grams}g of {selected_food_name}!")
    else:
        st.warning("No results found. Try a simpler term.")

# --- SECTION 2: WATER LOGGING ---
st.divider()
st.subheader("💧 Water Log")
col1, col2, col3 = st.columns([1,1,2])
if col1.button("+ 250ml"):
    new_w = pd.DataFrame([{"Date": today_str, "Liters": 0.25}])
    conn.update(worksheet="Water_Log", data=pd.concat([conn.read(worksheet="Water_Log", ttl=0), new_w]))
    st.rerun()
if col2.button("+ 500ml"):
    new_w = pd.DataFrame([{"Date": today_str, "Liters": 0.50}])
    conn.update(worksheet="Water_Log", data=pd.concat([conn.read(worksheet="Water_Log", ttl=0), new_w]))
    st.rerun()
