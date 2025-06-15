from src.map_funcs import load_data, summarise_and_plot
import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import json

if 'map_cache' not in st.session_state:
    st.session_state['map_cache'] = dict()  
    
st.set_page_config(layout='wide')

@st.cache_resource
def get_data():
    return load_data()

def generate_map(gdf, df, df_rent, date_range, home_type, beds, baths, parking):
    dictionary_lists = (date_range, home_type, beds, baths, parking)
    dictionary_key = (str(e) for e in dictionary_lists)

    if dictionary_key in st.session_state.map_cache:
        return st.session_state.map_cache[dictionary_key]

    map_element = summarise_and_plot(gdf, df, df_rent, date_range=date_range, home_type=home_type, beds=beds, baths=baths, parking=parking)
    
    st.session_state.map_cache = dict()
    st.session_state.map_cache[dictionary_key] = map_element
    folium.LayerControl().add_to(map_element)
    
    return map_element

st.sidebar.image('./data/logo/homerun-1.png')
df, gdf, df_rent = get_data()

st.sidebar.markdown("### Time Horizon")
colt1, colt2 = st.sidebar.columns(2)
start_date = colt1.text_input('Start', '2023-03-01')
end_date = colt2.text_input('End', df['date_sold'].max().strftime('%Y-%m-%d'))
date_range = (start_date, end_date)

st.sidebar.markdown("### Property Filters")
home_type = st.sidebar.multiselect('Home Type', options=list(df['home_type'].unique()), default=list(df['home_type'].unique()))
beds = st.sidebar.multiselect('Beds', options=sorted(df['beds'].dropna().unique()), default=sorted(df['beds'].dropna().unique()))
baths = st.sidebar.multiselect('Baths', options=sorted(df['baths'].dropna().unique()), default=sorted(df['baths'].dropna().unique()))
parking = st.sidebar.multiselect('Parking', options=sorted(df['parking'].dropna().unique()), default=sorted(df['parking'].dropna().unique()))

st.sidebar.markdown("### Suburb Filters")
min_school_decile = st.sidebar.slider('Minimum School Decile', min_value=int(gdf['decile_public_max'].min()), max_value=int(gdf['decile_public_max'].max()), value=8, step=1)

st.sidebar.markdown("#### Maximum commute times (minutes)")
col1, col2 = st.sidebar.columns(2)
max_train_time = float(col1.text_input('Train to Finity', '60'))
max_drive_time_padstow = float(col1.text_input('Drive to Padstow', '45'))
max_drive_time_kogarah = float(col2.text_input('Drive to Kogarah', '45'))
max_drive_time_tkmaxx = float(col2.text_input('Drive to TKMaxx', '45'))

tab1, tab2 = st.tabs(['Map', 'Data'])

with tab1:   
    if st.sidebar.button('Apply'):
        gdf_filtered = gdf[
            (gdf['decile_public_max'] >= min_school_decile) &
            (gdf['train_to_finity'] <= max_train_time) &
            (gdf['drive_to_padstow'] <= max_drive_time_padstow) &
            (gdf['drive_to_kogarah'] <= max_drive_time_kogarah) &
            (gdf['drive_to_tkmaxx'] <= max_drive_time_tkmaxx)
        ]
        m = generate_map(gdf_filtered, df, df_rent, date_range=date_range, home_type=home_type, beds=beds, baths=baths, parking=parking)

        folium_static(m, height=1100, width=2100)