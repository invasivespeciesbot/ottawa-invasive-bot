import requests 
import os 
from datetime import datetime
from atproto import Client 

# 1. SETUP & CONFIGURATION
INAT_BASE_URL = "https://inaturalist.org"
PLACE_ID = "27599"  # Ottawa Region

# FIXED: We use the exact taxon numerical IDs directly in the string
TAXON_IDS = "59778,130228,182246,914922" 

BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE') 
BSKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD') 

def run_bot(): 
    # Get today's date in YYYY-MM-DD format
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    # FIXED: Added a custom User-Agent to stop iNaturalist from blocking the script
    headers = {
        "User-Agent": "OttawaInvasiveSpeciesBot/1.0 (Contact: your_email@example.com)"
    }
    
    params = {
        "place_id": PLACE_ID,
        "taxon_id": TAXON_IDS,
        "quality_grade": "research",
        "created_d1": today_str,  
        "created_d2": today_str,  
        "per_page": 200,          
        "page": 1
    }

    # Initialize Bluesky client once 
    client = Client() 
    client.login(BSKY_HANDLE, BSKY_PASSWORD) 
    
    total_posted = 0

    while True:
        print(f"Fetching page {params['page']} from iNaturalist...")
        
        # FIXED: Passing both headers and params safely
        response = requests.get(INAT_BASE_URL, params=params, headers=headers)
        
        # FIXED: Check if the network request actually succeeded (HTTP 200)
        if response.status_code != 200:
            print(f"API Error! iNaturalist responded with Status Code: {response.status_code}")
            print(f"Response snippet: {response.text[:200]}")
            break

        # FIXED: Wrap JSON decoding inside a try/except block to protect against crashes
        try:
            data = response.json() 
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON. The API returned an empty or corrupted response.")
            print(f"Raw response text: {response.text[:500]}")
            break
        
        results = data.get('results', [])
        if not results:
            break  
            
        print(f"Found {len(results)} observations on page {params['page']}.")
        
        for obs in results: 
            taxon_info = obs.get('taxon', {}) 
            species = taxon_info.get('preferred_common_name', taxon_info.get('name', 'Unknown Species')) 
            location = obs.get('place_guess', 'Ottawa Region') 
            date = obs.get('observed_on', 'recently') 
            link = f"https://inaturalist.org{obs.get('id')}" 
            
            # Safely pull the Photo URL
            image_data = None 
            photos = obs.get('photos', []) 
            if photos and len(photos) > 0: 
                first_photo = photos[0]  # FIXED: Reference the list item correctly
                photo_url = first_photo.get('url', '') 
                if photo_url: 
                    if photo_url.startswith('//'): 
                        photo_url = 'https:' + photo_url 
                    photo_url = photo_url.replace('square', 'medium') 
                    try: 
                        image_data = requests.get(photo_url, headers=headers).content 
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
                
        if len(results) < params['per_page']:
            break
            
        params['page'] += 1

    if total_posted == 0:
        print("No new verified observations found for today.")
    else:
        print(f"Finished processing. Total posted: {total_posted}")

if __name__ == "__main__": 
    run_bot()
