import requests
import os
from atproto import Client

# 1. SETUP
INAT_URL = "https://api.inaturalist.org/v1/observations?place_id=27599&taxon_id=59778,130228,182246,914922&quality_grade=research&per_page=1"
BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE')
BSKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD')

def run_bot():
    response = requests.get(INAT_URL)
    data = response.json()

    if data.get('results') and len(data['results']) > 0:
        # FIX 1: Extract the first observation from the results list
        obs = data['results'][0]
        
        # Safely extract species name
        taxon_info = obs.get('taxon', {})
        species = taxon_info.get('preferred_common_name', taxon_info.get('name', 'Unknown Species'))
        
        location = obs.get('place_guess', 'Ottawa Region')
        date = obs.get('observed_on', 'recently')
        link = f"https://www.inaturalist.org/observations/{obs.get('id')}"
        
        # FIX 2 & 3: Safely pull the Photo URL from the photos list and fix missing https:
        image_data = None
        if obs.get('photos') and len(obs['photos']) > 0:
            photo_url = obs['photos']['url']
            if photo_url.startswith('//'):
                photo_url = 'https:' + photo_url
            photo_url = photo_url.replace('square', 'medium')
            
            try:
                image_data = requests.get(photo_url).content
            except Exception as e:
                print(f"Failed to download image: {e}")

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

        # 4. POST TO BLUESKY (With Image Fallback)
        client = Client()
        client.login(BSKY_HANDLE, BSKY_PASSWORD)
        
        if image_data:
            # Sends the text and the photo together safely
            client.send_image(text=message, image=image_data, image_alt=f"Photo of {species}")
            print("Post with photo sent successfully!")
        else:
            # Fallback to text-only post if the observation has no photos
            client.send_post(text=message)
            print("Post sent successfully (text only, no image found).")
    else:
        print("No new verified observations found.")

if __name__ == "__main__":
    run_bot()
