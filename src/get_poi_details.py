import googlemaps
import os
from dotenv import load_dotenv
import pandas as pd
import geopandas as gpd
from pathlib import Path
from utils.funcs import to_txt
import json 
from tqdm import tqdm

root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / '.env')

def get_poi_details(poi_str, cache_dir=root_dir / 'data/cache/maps-api/'):
    
    # Initialise and search
    gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
    
    try:
        search_result = gmaps.places(poi_str)
        place_id = search_result['results'][0]['place_id']
        place_details = gmaps.place(place_id=place_id)

        # Extracting required details
        details = place_details['result']['address_components']
        address_dict = {item['types'][0]: item['long_name'] for item in details}
        address = place_details['result'].get('formatted_address', '')
        street_number = address_dict.get('street_number', '')
        street_name = address_dict.get('route', '')
        suburb = address_dict.get('locality', '')
        postcode = address_dict.get('postal_code', '')
        location = place_details['result']['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']

        result = {
            'poi': poi_str.replace(', Sydney NSW', ''),
            'address': address,
            'street_number': street_number,
            'street_name': street_name,
            'suburb': suburb,
            'postcode': postcode,
            'latitude': latitude,
            'longitude': longitude
        }
        
        json_data = json.dumps(result, indent=4)
        file_path = cache_dir / f"{poi_str.replace(', Sydney NSW', '')}.json"
        with open(file_path, 'w') as file:
            file.write(json_data)
        
        # print(f'details saved: {file_path}')

    except Exception as e:
        result = {
            'poi': None,
            'address': None,
            'street_number': None,
            'street_name': None,
            'suburb': None,
            'postcode': None,
            'latitude': None,
            'longitude': None
        }

    return result

def main():
    df = pd.read_excel(root_dir / 'data/geo/pois.xlsx', sheet_name='pois')
    pois = [poi + ', Sydney NSW' for poi in df['poi'].to_list()]
    geo_data = [get_poi_details(poi) for poi in tqdm(pois, 'processing')]
    geo_data_df = pd.DataFrame(geo_data)
    geo_data_df = pd.merge(geo_data_df, df[['poi', 'public_school_percentile']], how='left', on='poi')
    geo_data_df.to_csv(root_dir/'data/geo/pois_processed.csv')

if __name__ == '__main__':
    main()
    


