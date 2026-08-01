import requests 
import os 
from datetime import datetime
from atproto import Client 

# 1. SETUP & CONFIGURATION
# We remove the fixed 'per_page=3' and dynamically add date bounds later
INAT_BASE_URL = "https://inaturalist.org"
PLACE_ID = "27599"  # Ottawa Region
TAXON_IDS = "59778,130228,182246,914922" # Target species

BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE') 
BSKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD') 

def run_bot(): 
    # Get today's date in YYYY-MM-DD format
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    # Build query parameters to filter precisely by today's upload date
    params = {
        "place_id": PLACE_ID,
        "taxon_id": TAXON_IDS,
        "quality_grade": "research",
        "created_d1": today_str,  # Start of upload date range
        "created_d2": today_str,  # End of upload date range
        "per_page": 200,          # Maximize results per API call to minimize pages
        "page": 1
    }

    # Initialize Bluesky client once 
    client = Client() 
    client.login(BSKY_HANDLE, BSKY_PASSWORD) 
    
    total_posted = 0

    while True:
        print(f"Fetching page {params['page']} from iNaturalist...")
        response = requests.get(INAT_BASE_URL, params=params)
        data = response.json() 
        
        results = data.get('results', [])
        if not results:
            break  # Stop looping if the current page has no results
            
        print(f"Found {len(results)} observations on page {params['page']}.")
        
        for obs in results: 
            taxon_info = obs.get('taxon', {}) 
            species = taxon_info.get('preferred_common_name', taxon_info.get('name', 'Unknown Species')) 
            location = obs.get('place_guess', 'Ottawa Region') 
            date = obs.get('observed_on', 'recently') 
            link = f"https://inaturalist.org/{obs.get('id')}/" 
            
            # Safely pull the Photo URL
            image_data = None 
            photos = obs.get('photos', []) 
            if photos and len(photos) > 0: 
                first_photo = photos[0] 
                photo_url = first_photo.get('url', '') 
                if photo_url: 
                    if photo_url.startswith('//'): 
                        photo_url = 'https:' + photo_url 
                    photo_url = photo_url.replace('square', 'medium') 
                    try: 
                        image_data = requests.get(photo_url).content 
                    except Exception as e: 
                        print(f"Failed to download image for ID {obs.get('id')}: {e}") 
            
            # 2. CUSTOM CAPTION LOGIC 
            if species == "Wild Parsnip": 
                warning = "⚠️ Caution: Sap causes severe skin burns in sunlight. Avoid contact!" 
            elif species == "Giant Hogweed": 
                warning = "🚨 Danger: Extremely toxic! Sap causes blistering burns. Do not touch!" 
            elif species == "Japanese Knotweed": 
                warning = "🏠 Eco-Alert: Highly invasive. Can damage house foundations and roads." 
            elif species == "Dog-strangling Vine": 
                warning = "🦋 Eco-Alert: Crowds out native plants and harms Monarch butterflies." 
            else: 
                warning = "🌿 Give this invasive species space and report it to local authorities." 
            
            # 3. BUILD THE MESSAGE 
            message = ( 
                f"New {species} spotted in {location} ({date}).\n\n" 
                f"{warning}\n\n" 
                f"Details: {link} #Ottawa #InvasiveSpecies" 
            ) 
            
            # 4. POST TO BLUESKY 
            try:
                if image_data: 
                    client.send_image(text=message, image=image_data, image_alt=f"Photo of {species}") 
                else: 
                    client.send_post(text=message) 
                
                total_posted += 1
                print(f"Successfully posted observation ID {obs.get('id')}.")
            except Exception as e:
                print(f"Failed to post observation {obs.get('id')} to Bluesky: {e}")
                
        # If the number of results is less than the max per page, we've hit the last page
        if len(results) < params['per_page']:
            break
            
        # Move to the next page of results
        params['page'] += 1

    if total_posted == 0:
        print("No new verified observations found for today.")
    else:
        print(f"Finished processing. Total posted: {total_posted}")

if __name__ == "__main__": 
    run_bot()
