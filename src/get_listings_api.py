# import geopandas as gpd
from src.utils.tg import send_telegram_message
# from tqdm import tqdm
import requests
import json
from pandas import json_normalize
from datetime import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

root_dir = Path(__file__).parent.parent

DOMAIN_API_KEY = os.getenv('DOMAIN_API_KEY')

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def get_listings(suburb, postcode, state='NSW', include_surrounding_suburbs=True, listing_type='Rent', page_size=100, page_number=1, api_key=DOMAIN_API_KEY, return_table=False):
    v_search = 'https://api.domain.com.au/v1/listings/residential/_search'
    v_body = {
        "listingType": listing_type,
        "locations": [
        {
            "state": state,
            "suburb": suburb,
            "postcode": str(postcode),
            "includeSurroundingSuburbs": include_surrounding_suburbs
        }
        ], 
        "excludePriceWithheld": False,
        "excludeDepositTaken": True,
        "pageSize": page_size,
        "pageNumber": page_number
    }
    headers = {'X-API-Key': api_key}
        
    try:
        response = requests.post(v_search, headers=headers, data=json.dumps(v_body))
        response.raise_for_status() # Raise an exception for HTTP errors
        df = json_normalize(response.json())
        timestamp = datetime.strftime(datetime.now(), '%Y%m%d')
        # db = DropboxAPI() # Removed DropboxAPI instantiation
        # db_dir = '/edhff/domain-listings-api/' # Old Dropbox path
        
        file_name = f"{suburb}_{postcode}_{timestamp}.csv"
        local_dir = root_dir / f"data/domain/listings-api/{listing_type.lower()}/{timestamp}/"
        local_file_path = local_dir / file_name
        
        ensure_dir(local_file_path)
        df.to_csv(local_file_path, index=False)
        
        if return_table:
            return df

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - {response.status_code} - {response.text}")
    except Exception as e:
        print(f"error: {e}")
        pass

# def get_suburb_list():
#     gdf = gpd.read_feather('./data/geo/gdf_final.feather')
#     suburbs = gdf[['suburb', 'postcode']].reset_index(drop=True)
#     suburbs['suburb'] = suburbs['suburb'].apply(lambda x: x.upper())
#     return suburbs

def get_suburb_shortlist():
    df = pd.read_excel(root_dir/'data/domain-listing-counts.xlsx', sheet_name='data')
    df_filtered = df[df['shortlist']==1]
    suburbs = df_filtered[['suburb', 'postcode']].reset_index(drop=True)
    suburbs['suburb'] = suburbs['suburb'].apply(lambda x: x.upper())
    return suburbs
  
def collate_listings(datestamp=datetime.strftime(datetime.now(), '%Y%m%d')):
    # db = DropboxAPI() # Removed DropboxAPI instantiation
    send_telegram_message('collating sales', production_mode=True, chat_group='updates')
    
    source_directory_path = root_dir / f'data/domain/listings-api/sale/{datestamp}/'
    all_files_data = []

    if not source_directory_path.exists():
        print(f"Source directory {source_directory_path} does not exist. No files to collate.")
        send_telegram_message(f'Error: Source directory {source_directory_path} not found for collation.', production_mode=True, chat_group='updates')
        return

    for file_name in os.listdir(source_directory_path):
        if file_name.endswith('.csv'):
            file_path = source_directory_path / file_name
            try:
                df_temp = pd.read_csv(file_path)
                all_files_data.append(df_temp)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    if not all_files_data:
        print(f"No CSV files found or read from {source_directory_path}.")
        send_telegram_message(f'No sales data to collate for {datestamp}.', production_mode=True, chat_group='updates')
        return
        
    df_raw = pd.concat(all_files_data, ignore_index=True)
    
    collated_dir_path = root_dir / 'data/domain/listings-api/sale/collated/'
    collated_file_path = collated_dir_path / f'sales_{datestamp}.csv'
    
    ensure_dir(collated_file_path)
    df_raw.to_csv(collated_file_path, index=False)
    
    send_telegram_message(f'sales collated to {collated_file_path}', production_mode=True, chat_group='updates')

def get_current_sales_listings():
    suburbs = get_suburb_shortlist()
    
    for index, row in suburbs.iterrows():
        # get_listings(row['suburb'], row['postcode'])
        if index % 20 == 0:
            send_telegram_message(f'getting suburb sales: {index} of {suburbs.shape[0]}', production_mode=True, chat_group='updates')
        get_listings(row['suburb'], row['postcode'], listing_type='Sale')

    collate_listings()
    return

if __name__ == '__main__':
    get_current_sales_listings()
