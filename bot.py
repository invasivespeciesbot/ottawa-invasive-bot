import requests 
import os 
from atproto import Client 

# 1. SETUP & CONFIGURATION
INAT_BASE_URL = "https://api.inaturalist.org/v1/observations?place_id=27599&taxon_id=59778,130228,182246,914922&quality_grade=research&per_page=10"
PLACE_ID = "27599"  # Ottawa Region
TAXON_IDS = "59778,130228,182246,914922" 

BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE') 
BSKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD') 

HISTORY_FILE = "posted_ids.txt"

def load_posted_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_posted_id(obs_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{obs_id}\n")

def run_bot(): 
    posted_ids = load_posted_ids()
    
    headers = {
        "User-Agent": "OttawaInvasiveSpeciesBot/1.0 (Contact: your_email@example.com)"
    }
    
    # FETCH RECENT RECORDS (No strict day boundaries, sorted by newest)
    params = {
        "place_id": PLACE_ID,
        "taxon_id": TAXON_IDS,
        "quality_grade": "research",
        "order_by": "created_at",
        "order": "desc",
        "per_page": 20,          
        "page": 1
    }

    client = Client() 
    client.login(BSKY_HANDLE, BSKY_PASSWORD) 
    
    total_posted = 0

    print(f"Fetching latest observations from iNaturalist...")
    response = requests.get(INAT_BASE_URL, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"API Error! Status Code: {response.status_code}")
        return

    try:
        data = response.json() 
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON response.")
        return
    
    results = data.get('results', [])
    print(f"Found {len(results)} total recent candidate observations.")
    
    for obs in results: 
        obs_id = str(obs.get('id'))
        
        # Skip if we already posted it in ANY past run
        if obs_id in posted_ids:
            print(f"Skipping ID {obs_id}: Already posted previously.")
            continue

        taxon_info = obs.get('taxon', {}) 
        species = taxon_info.get('preferred_common_name', taxon_info.get('name', 'Unknown Species')) 
        location = obs.get('place_guess', 'Ottawa Region') 
        date = obs.get('observed_on', 'recently') 
        link = f"https://inaturalist.org{obs_id}" 
        
        # Pull Photo URL
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
                    image_data = requests.get(photo_url, headers=headers).content 
                except Exception as e: 
                    print(f"Failed to download image for ID {obs_id}: {e}") 
        
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
            
            save_posted_id(obs_id)
            total_posted += 1
            print(f"Successfully posted observation ID {obs_id}.")
        except Exception as e:
            print(f"Failed to post observation {obs_id} to Bluesky: {e}")
            
    print(f"Finished processing. Total posted this run: {total_posted}")

if __name__ == "__main__": 
    run_bot()
