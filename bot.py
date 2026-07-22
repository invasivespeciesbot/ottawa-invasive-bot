import requests
import os
from atproto import Client

# 1. SETUP: These tell the bot where to look and who to post as
INAT_URL = "https://api.inaturalist.org/v1/observations?place_id=27599&taxon_id=59778,130228,182246,914922&quality_grade=research&per_page=1"
BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE')
BSKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD')

def run_bot():
    # 2. REQUEST DATA: This "hits" the iNaturalist API for the latest sightings
    response = requests.get(INAT_URL)
    data = response.json()

    # 3. FILTER & EXTRACT: Select the first result  from the list
    if data['results']:
        # This line was fixed to select the first item in the list:
        obs = data['results'] 
        
        species = obs['taxon']['preferred_common_name']
location = obs['place_guess']
date = obs['observed_on']
link = f"https://www.inaturalist.org/observations/{obs['id']}"

        # 4. POST TO BLUESKY: Creating the message using your template
        client = Client()
        client.login(BSKY_HANDLE, BSKY_PASSWORD)
        
        message = (
            f"🌿 New {species} spotted near {location} on {date}. "
            f"Give it space — sap can cause skin burns. "
            f"Details: {link} #OttawaHikers #InvasiveSpecies"
        )
        
        client.send_post(message)
        print("Post sent successfully!")
    else:
        print("No new observations found.")

if __name__ == "__main__":
    run_bot()
