import requests
import os
from atproto import Client

# 1. SETUP: This pulls from the IDs you found in Phase 1
INAT_URL = "https://api.inaturalist.org/v1/observations?place_id=27599&taxon_id=59778,130228,182246,914922&quality_grade=research&per_page=1"
BSKY_HANDLE = os.environ.get('BLUESKY_HANDLE')
BSKY_PASSWORD = os.environ.get('BLUESKY_PASSWORD')

def run_bot():
    # 2. REQUEST DATA: Hits the iNaturalist API
    response = requests.get(INAT_URL)
    data = response.json()

    # 3. FILTER & EXTRACT: Using only "research grade" for accuracy
    if data.get('results') and len(data['results']) > 0:
        # Pick the first result from the list using index [0]
        obs = data['results'][0]
        
        # Safely pull fields using .get() to prevent crashes if a name or guess is missing
        taxon_info = obs.get('taxon', {})
        species = taxon_info.get('preferred_common_name', taxon_info.get('name', 'Unknown Species'))
        location = obs.get('place_guess', 'Ottawa Region')
        date = obs.get('observed_on', 'recently')
        link = f"https://www.inaturalist.org/observations/{obs.get('id')}"

        # 4. POST TO BLUESKY: Using the required safety template
        client = Client()
        client.login(BSKY_HANDLE, BSKY_PASSWORD)
        
        message = (
            f"🌿 New {species} spotted near {location} on {date}. "
            f"Give it space — sap can cause skin burns. "
            f"Details: {link} #OttawaHikers #InvasiveSpecies"
        )
        
        client.send_post(text=message)
        print("Post sent successfully!")
    else:
        print("No new verified observations found.")

if __name__ == "__main__":
    run_bot()
