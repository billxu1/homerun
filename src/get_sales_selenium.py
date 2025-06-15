from selenium.webdriver.common.by import By
import pandas as pd
from datetime import datetime
# from utils.uc import safe_find_element, set_up_driver
# from utils.tg import send_telegram_message
import geopandas as gpd
import requests
import pytz
import os

from src.utils.uc import safe_find_element, set_up_driver
from src.utils.tg import send_telegram_message


timezone = pytz.timezone('Australia/Sydney')

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_listing(locality, page, driver):
    link = f"https://www.domain.com.au/sold-listings/{locality}/?excludepricewithheld=1&ssubs=0&page={page}"
    print(link)
    datestamp = datetime.now(timezone).strftime("%Y%m%d")
    page_0 = '{:02d}'.format(page)    
    
    for attempt in range(3):
        if attempt > 0:
            send_telegram_message(f"{locality}: page {page} - {len(listings)} listings - attempt {attempt+1}") 
        driver.get(link)
        listings = driver.find_elements(By.CLASS_NAME, 'css-1qp9106')
        if len(listings) == 20:
            break
        else:
            # Create an empty DataFrame or handle as per original logic if df is defined earlier
            # For now, assuming df might not be defined here, so creating an empty one for error logging.
            error_df = pd.DataFrame() 
            error_file_path = f"./data/domain/sales-selenium/errors/{locality}_{page_0}.csv"
            ensure_dir(error_file_path)
            error_df.to_csv(error_file_path, index=False)
    
    data = []
    # listings = driver.find_elements(By.CLASS_NAME, 'css-1qp9106')
    send_telegram_message(f"{locality}: page {page} - {len(listings)} listings")
    
    for listing in listings:
        price = safe_find_element(listing, By.CSS_SELECTOR, "[data-testid='listing-card-price']", remove_text=' price from APM PriceFinder')
        link = safe_find_element(listing, By.CSS_SELECTOR, "a[href]", 'href')
        print(f"--- {link}")
        address_line1 = safe_find_element(listing, By.CSS_SELECTOR, "[data-testid='address-line1']", remove_text=',')
        address_line2 = safe_find_element(listing, By.CSS_SELECTOR, "[data-testid='address-line2']")
        
        try:
            property_features = listing.find_element(By.CSS_SELECTOR, "[data-testid='property-features']")         
            beds = safe_find_element(property_features, By.CSS_SELECTOR, "[data-testid='property-features-feature']:nth-child(1)", remove_text= '\nBeds')
            bath = safe_find_element(property_features, By.CSS_SELECTOR, "[data-testid='property-features-feature']:nth-child(2)", remove_text='\nBaths|\nBath')
            parking = safe_find_element(property_features, By.CSS_SELECTOR, "[data-testid='property-features-feature']:nth-child(3)", remove_text='\nParking')
        except Exception:
            beds, bath, parking = None, None, None
            
        try:
            sqm = safe_find_element(property_features, By.CSS_SELECTOR, "[data-testid='property-features-feature']:nth-child(4)")
            sqm = sqm.replace('m²', '') if sqm else None
        except Exception:
            sqm = None
            
        home_type = safe_find_element(listing, By.CLASS_NAME, "css-11n8uyu")
        if home_type:
            home_type = home_type.replace('Apartment / Unit / Flat', 'Unit')

        img_links = [img.get_attribute('src') for img in listing.find_elements(By.CSS_SELECTOR, "[data-testid='listing-card-lazy-image'] img")]
                            
        sold_by = safe_find_element(listing, By.CSS_SELECTOR, "[data-testid='listing-card-branding'] img", 'alt', remove_text='Logo for ')
        method_and_date_sold = safe_find_element(listing, By.CSS_SELECTOR, "[data-testid='listing-card-tag'] span")

        data.append([link, price, address_line1, address_line2, beds, bath, parking, sqm, home_type, img_links, sold_by, method_and_date_sold])

    df = pd.DataFrame(data, columns=['link','price', 'address1', 'address2', 'beds', 'baths', 'parking', 'sqm', 'home_type', 'image_links', 'sold_by', 'method_and_date_sold'])
    df['method_sold'] = df['method_and_date_sold'].apply(lambda x: x[:-12].replace('SOLD ', '').strip().title())
    df['date_sold'] = pd.to_datetime(df['method_and_date_sold'].str[-11:], format='%d %b %Y')
    df['price'] = df['price'].replace({'\$': '', ',': ''}, regex=True).astype(int)

    # db = DropboxAPI() # Removed DropboxAPI instantiation
    
    output_file_path = f"./data/domain/sales-selenium/{locality}_{page_0}_{datestamp}.csv"
    ensure_dir(output_file_path)
    df.to_csv(output_file_path, index=False)

    return df

def get_listing_error_handled(locality, page, driver):
    try:
        df = get_listing(locality, page, driver)
    except Exception as e:
        df = pd.DataFrame(columns=['link', 'price', 'address1', 'address2', 'beds', 'baths', 'parking', 'sqm', 'home_type', 'image_links', 'sold_by', 'method_and_date_sold'])
        # db = DropboxAPI() # Removed DropboxAPI instantiation
        page_0 = '{:02d}'.format(page)
        error_file_path = f"./data/domain/sales-selenium/errors/{locality}_{page_0}.csv"
        ensure_dir(error_file_path)
        df.to_csv(error_file_path, index=False)
    finally:
        return df

def get_listings(localities, pages=50, start=1, date_cutoff='2021-07-01'):
       
    send_telegram_message(f"scraping {localities}, pages {start}-{start+pages-1}")
    
    df_all = [] 

    if not isinstance(localities, list):
        localities = [localities]
    
    cutoff_date = pd.to_datetime(date_cutoff)

    for i, locality in enumerate(localities):
        send_telegram_message(f"{i} of {len(localities)} - {locality}")
        driver = set_up_driver()
        
        for page in range(start, pages + start):
            if page == 26:
                driver.close()
                driver = set_up_driver()

            df = get_listing_error_handled(locality, page, driver)
            df_all.append(df)
            
            try:
                if df['date_sold'].min() < cutoff_date or page == 50:
                    send_telegram_message(f"scraped to: {df['date_sold'].min()}")
                    break
            except Exception as e:
                pass
                            
        driver.close()
        
    return pd.concat(df_all)

def get_localities(from_gdf=False):
    if from_gdf:
        gdf = gpd.read_feather('./data/geo/gdf_filtered.feather')
        return gdf.apply(lambda row: f"{row['suburb'].lower().replace(' ','-')}-nsw-{row['postcode']}", axis=1).to_list()
    else:
        df = pd.read_excel('./data/domain/domain-listing-counts.xlsx', sheet_name='data')
        df = df[df['scrape'] > 0]
        return df['locality'].to_list()

def get_listing_count(locality, driver):
    link = f"https://www.domain.com.au/sold-listings/{locality}/?excludepricewithheld=1&ssubs=0"
    driver.get(link)

    try:
        listing_text = driver.find_element(By.CLASS_NAME, "css-ekkwk0").text
        listings = listing_text.split(sep=' ')[0]
    except Exception as e:
        listings = -1
    finally:
        print(f"{locality}: {listings}")
        return {'locality':locality, 'listings':listings}
    
def get_listing_counts(localities, n_driver_reset=30):
    count = 0
    driver = set_up_driver()
    # db = DropboxAPI() # Removed DropboxAPI instantiation
    
    result = []
    for locality in localities:
        result.append(get_listing_count(locality, driver))

        count += 1
        if count % n_driver_reset == 0:
            driver.close()
            driver = set_up_driver()
            output_file_path = './data/domain/sales-selenium/domain-listing-counts.csv'
            ensure_dir(output_file_path)
            pd.DataFrame(result).to_csv(output_file_path, index=False)
            
    driver.close()
    # Final save if not saved in loop
    output_file_path = './data/domain/sales-selenium/domain-listing-counts.csv'
    ensure_dir(output_file_path)
    pd.DataFrame(result).to_csv(output_file_path, index=False)
    return result

def collate_files():
    # db = DropboxAPI() # Removed DropboxAPI instantiation
    source_directory = './data/domain/sales-selenium/'
    # Ensure the source directory itself exists, though listdir won't fail if it's empty or doesn't exist (returns error)
    if not os.path.exists(source_directory):
        print(f"Source directory {source_directory} does not exist. No files to collate.")
        return

    files = [f for f in os.listdir(source_directory) if f.endswith('.csv') and not os.path.basename(f).startswith('collated_sales') and not os.path.basename(f).startswith('domain-listing-counts') and 'errors' not in f]
    
    if not files:
        print(f"No CSV files found in {source_directory} to collate.")
        return

    all_files_data = []
    for file_name in files:
        file_path = os.path.join(source_directory, file_name)
        try:
            all_files_data.append(pd.read_csv(file_path))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    if not all_files_data:
        print("No dataframes to concatenate.")
        return

    df = pd.concat(all_files_data, ignore_index=True) # Use ignore_index=True if original indices are not important
    
    collated_file_path = os.path.join(source_directory, 'collated_sales.csv')
    ensure_dir(collated_file_path) # ensure_dir will handle the directory part
    df.to_csv(collated_file_path, index=False)
    print(f"Collated data saved to {collated_file_path}")
    return

def get_latest_sales():
    url = 'https://api.domain.com.au/v1/salesResults/Sydney/listings'

    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer 3da1f8d95a4662681e80be82fa3a5a56',
    }

    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json()) 

def main():
    localities = get_localities()
    df = get_listings(localities[0], date_cutoff='2025-01-01')
    collate_files()
    return

if __name__ == "__main__":
    main()
