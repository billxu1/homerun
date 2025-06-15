
import geopandas as gpd
import pandas as pd
import folium
from folium.features import GeoJsonTooltip
from branca.colormap import linear
import warnings
import os
import re

warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS', UserWarning)

def clean_home_type(df):
    home_type_dict = {
        "Unit": "Unit",
        "House": "House",
        "Townhouse": "Townhouse",
        "Semi": "Townhouse",
        "Duplex": "Townhouse",
        "Studio": "Unit",
        "Terrace": "Townhouse",
        "Villa": "Townhouse",
        "Cottage": "Townhouse",
        "Semi-detached": "Townhouse",
        "Retirement Living": "House",
        "New apartments / off the plan": "Unit",
        "Flat": "Unit",
        "New house and land": "House"
    }
    df['home_type'] = df['home_type'].replace(home_type_dict)
    df = df[~df['home_type'].isin(["Block of units", "New land", "Rural"])]
    return df

def clean_fields(df):
    
    # Locality
    df['suburb'] = df['suburb'].apply(lambda x: x.title())
    df.loc[df['suburb'] == 'Mcmahons Point', 'suburb'] = 'North Sydney'
    df['key'] = df['suburb'] + " - " + df['postcode'].astype(int).astype(str)
    df['key'] = df['key'].astype(str)
    
    # Beds, bath parking
    df['beds'] = df['beds'].apply(lambda x: max(min(x, 5),1))
    df['baths'] = df['baths'].apply(lambda x: max(min(x, 5), 1))
    df['parking'].replace({"−": 0, pd.NA: 0}, inplace=True)
    df['parking'] = df['parking'].apply(lambda x: min(x, 2))
    
    # Clean fields
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    
    # print(f"removing rows with na price: {df['price'].isna().sum()}")
    df = df.dropna(subset=['price'])
    # print(f"removing rows with missing postcode: {df['postcode'].isna().sum()}")
    df = df.dropna(subset=['postcode'])
  
    return df

def load_sales_data():
    print("loading sales data")
    df = pd.read_csv('./data/domain/sales.csv')
    df['date_sold'] = pd.to_datetime(df['date_sold'])
    df = clean_fields(df)
    return clean_home_type(df)

def load_geo_data():
    print("loading geo data")
    gdf = gpd.read_feather('./data/geo/gdf_final.feather')
    return gdf.drop(columns='centroid')

def load_school_data():
    print("loading school data")
    schools = pd.read_excel('data/geo/naplan-scores-2022.xlsx', sheet_name = 'final')
    suburb_map = pd.read_csv('data/geo/suburb_pc.csv')
    schools['suburb'] = schools['suburb'].apply(lambda x: re.sub(' North| South| East| West', '', x))
    schools = pd.merge(schools, suburb_map, how='left', on='suburb')
    schools = schools[~schools['postcode'].isna()]
    schools['postcode'] = schools['postcode'].astype(int)
    schools = schools[(schools['state']=='NSW') & (schools['postcode'] < 2250)]
    schools['key'] = schools['suburb'] + " - " + schools['postcode'].astype(str)
    schools.set_index('key', inplace=True)
    return schools.drop(columns=['suburb', 'postcode', 'state', 'decile_diff'])

def load_rent_data():
    print("loading rent data")
    df = pd.read_csv('./data/domain/rent.csv')

    return clean_fields(df)

def load_data():
    df = load_sales_data()
    gdf = load_geo_data()
    schools = load_school_data()
    df_rent = load_rent_data()
    
    gdf = gdf.join(schools, on='key', how='left')
    gdf = gdf.fillna(0)
    
    # print(f"dim df: {df.shape}")
    # print(f"dim gdf: {gdf.shape}")
    
    return df, gdf, df_rent

def prepare_gdf(gdf, summary, summary_rent):
    gdf_comb = gdf.join(summary, how='left')
    gdf_comb = gdf_comb.join(summary_rent, how='left')
    
    gdf_comb['yield_median'] = round(gdf_comb['median_rent'] * 52 / gdf_comb['median_price'], 4)
    gdf_comb['yield_q1'] = round(gdf_comb['rent_q1'] * 52 / gdf_comb['price_q1'], 4)
    gdf_comb['yield_q3'] = round(gdf_comb['rent_q3'] * 52 / gdf_comb['price_q3'], 4)
    
    return gdf_comb.reset_index()

def summarise_data(df, round_digits=-3, date_filter=True, date_range=None, home_type=None, beds=None, baths=None, parking=None, suffix=None):
    
    # df.to_csv(f'./temp/df_{suffix}_original.csv')
    
    # Applying filters based on the provided parameters
    if date_filter and date_range is not None:
        df = df.loc[(df['date_sold'] >= date_range[0]) & (df['date_sold'] <= date_range[1])]

    filters = {'home_type': home_type, 'beds': beds, 'baths': baths, 'parking': parking}
    for column, condition in filters.items():
        if condition is not None:
            df = df.loc[df[column].isin(condition)]

    # df.to_csv(f'./temp/df_{suffix}_filtered.csv')

    # Group by 'key' and calculate the percentiles and count of records
    summary = df.groupby('key').agg({
        'price': [lambda x: x.quantile(0.10), lambda x: x.quantile(0.25), 'median', lambda x: x.quantile(0.75), lambda x: x.quantile(0.90)],
        'key': 'count'
    })
    

    # Rename and round the price columns
    summary.columns = ['price_p10', 'price_q1','median_price', 'price_q3', 'price_p90', 'properties']
    for col in ['price_p10', 'price_q1','median_price', 'price_q3', 'price_p90']:
        summary[col] = summary[col].apply(lambda x: round(x, round_digits))

    # summary.to_csv(f'./temp/df_{suffix}_summarised.csv')
    
    return summary

def plot_map(gdf_comb):
    
    # Base map
    m = folium.Map(location=[gdf_comb.geometry.centroid.y.mean(), gdf_comb.geometry.centroid.x.mean()], zoom_start=12)
    
    # Colour Map
    colormap = linear.YlOrRd_09.scale(800000, 2500000)
    colormap.caption = 'Median Price'
    m.add_child(colormap)

    # Define tooltip
    tooltip = GeoJsonTooltip(
        fields=['key', 'price_p10', 'price_q1', 'median_price', 'price_q3', 'price_p90', 'properties', 
                'median_rent', 'rental_properties', 'yield_median', 
                'decile_public_average', 'decile_public_max', 'schools', 'seifa', 'train_to_finity', 'drive_to_padstow', 'drive_to_kogarah', 'drive_to_tkmaxx'],
        aliases=['Suburb: ', 'P10 Price', 'Q1 Price', 'Median Price: ', 'Q3 Price', 'P90 Price', 'Properties Sold: ', 
                 'Median Rent', 'Rental Properties', 'Median Yield', 
                 'Decile Public Avg: ', 'Decile Public Max: ', 'Schools: ', 'SEIFA: ', 'Finity: ', 'Padstow ', 'Kogarah ', 'TK: '],
        localize=True
    )

    # Function to return color given feature
    def style_function(feature):
        median_price = feature['properties']['median_price']
        decile_public_average = feature['properties']['decile_public_average']

        border_color = '#151515' if decile_public_average in [8, 9, 10] else '#000000'
        border_weight = 1 if decile_public_average in [9, 10] else 0

        return {
            'fillOpacity': 0.3,
            'weight': border_weight,
            'color': border_color,
            'fillColor': '#black' if median_price is None else colormap(median_price)
        }

    # Add the colored layer
    folium.GeoJson(gdf_comb, style_function=style_function, tooltip=tooltip).add_to(m)

    return m

def summarise_and_plot(gdf, df, df_rent, **kwargs):
    summary = summarise_data(df, suffix='sales', **kwargs)
    summary_rent = summarise_data(df_rent, suffix='rent', round_digits=0, date_filter=False, **kwargs)
    summary_rent.rename(columns={
        'median_price': 'median_rent',
        'price_p10': 'rent_p10',
        'price_q1': 'rent_q1',
        'price_q3': 'rent_q3',
        'price_p90': 'rent_p90',
        'properties': 'rental_properties'
    }, inplace=True)
    
    gdf_comb = prepare_gdf(gdf, summary, summary_rent)
    
    # summary.to_csv('./temp/summary.csv')
    # summary_rent.to_csv('./temp/summary_rent.csv')
    # gdf_comb.drop(columns=['geometry']).to_csv('./temp/gdf_comb.csv', index=False)
    # df.to_csv('./temp/sales.csv')
    
    return plot_map(gdf_comb)

def main():
    
    df, gdf, df_rent = load_data()
    summarise_and_plot(gdf,
                        df, 
                        df_rent,
                        date_range = ('2023-04-01', '2023-06-30'),
                        home_type = ['Townhouse', 'House'],
                        beds = [1, 2, 3, 4],
                        baths = None,
                        parking = None)

