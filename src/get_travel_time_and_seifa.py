import os
from dotenv import load_dotenv
import googlemaps
import pandas as pd
import geopandas as gpd
load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GPLACES_API_KEY"))

def load_geo_data():
    gdf = gpd.read_feather('../data/geo/gdf_metro.feather')
    gdf['suburb'] = gdf['suburb'].apply(lambda x: x.title())
    gdf['key'] = gdf['suburb'] + " - " + gdf['postcode'].astype(str)
    gdf = gdf.to_crs('EPSG:3857')
    gdf['centroid'] = gdf['geometry'].centroid.to_crs('EPSG:4326')
    gdf.set_index('key', inplace=True)
    return gdf.to_crs('EPSG:4326') 

def get_travel_time(origin, destination, mode):
    try:
        directions_result = gmaps.directions(origin, destination, mode=mode, departure_time="now")
        if len(directions_result) > 0:
            travel_time_text = directions_result[0]['legs'][0]['duration']['text']
            travel_time_value = directions_result[0]['legs'][0]['duration']['value']
            if "hour" in travel_time_text:
                # Convert hours to minutes
                hours = int(travel_time_text.split(" hour")[0])
                minutes = int(travel_time_text.split(" hour ")[1].split(" min")[0])
                travel_time_minutes = hours * 60 + minutes
            else:
                # Travel time is given in minutes
                travel_time_minutes = int(travel_time_value / 60)
            return travel_time_minutes
        else:
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_duration_batch(destination, mode, coordinates_list):
    result = []
    for i, coordinates in enumerate(coordinates_list):
        duration = get_travel_time(coordinates, destination, mode)
        result.append(duration)
        print(f"{i}: {duration}")
    return result

def attach_durations():
    gdf = load_geo_data()
    coordinates_list = [(point.y, point.x) for point in gdf['centroid']]
    
    train_to_finity = get_duration_batch("68 Harrington Street THE ROCKS NSW 2000", "transit", coordinates_list)
    drive_to_padstow = get_duration_batch("2 Blanche Avenue Padstow NSW 2211", "driving", coordinates_list)
    drive_to_kogarah = get_duration_batch("133 Harrow Rd, Kogarah NSW 2217", "driving", coordinates_list)
    drive_to_tkmaxx = get_duration_batch("189 O'Riordan St, Mascot NSW 2020", "driving", coordinates_list)
    
    gdf['train_to_finity'] = train_to_finity
    gdf['drive_to_padstow'] = drive_to_padstow
    gdf['drive_to_kogarah'] = drive_to_kogarah
    gdf['drive_to_tkmaxx'] = drive_to_tkmaxx

    path_out = '../data/geo/gdf_with_durations.feather'
    gdf.to_feather(path_out)
    print(f"gdf saved: {path_out}")

def attach_seifa():
        
    gdf = gpd.read_feather('./data/geo/gdf_with_durations.feather')
    df_seifa = pd.read_excel('./data/geo/seifa.xlsx', sheet_name='processed')

    gdf2 = gdf.merge(df_seifa, on='suburb', how='left')
    postcode_means = gdf2.groupby('postcode')['seifa'].mean()

    # Impute missing SEIFA values with the postcode average
    gdf2['seifa'] = gdf2.apply(lambda row: postcode_means[row['postcode']] if pd.isna(row['seifa']) else row['seifa'], axis=1)

    gdf2['key'] = gdf2['suburb'] + " - " + gdf2['postcode'].astype(str)
    gdf2.set_index('key', inplace=True)

    path_out = './data/geo/gdf_final.feather'
    gdf2.to_feather(path_out)
    print(f"gdf saved: {path_out}")

def main():
    attach_durations()
    attach_seifa()
    return

if __name__ == 'main':
    main()