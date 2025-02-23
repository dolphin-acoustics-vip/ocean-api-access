import os
import requests

# API URLs
BASE_URL = "https://research.st-andrews.ac.uk/ocean/api"
SELECTIONS_ENDPOINT = f"{BASE_URL}/metadata/selections/"
ENCOUNTERS_ENDPOINT = f"{BASE_URL}/metadata/encounters/"
RECORDINGS_ENDPOINT = f"{BASE_URL}/metadata/recordings/"
FILES_ENDPOINT = f"{BASE_URL}/filespace/file/"
SPECTROGRAM_ENDPOINT = f"{BASE_URL}/filespace/spectrogram/"
AUTH_ENDPOINT = f"{BASE_URL}/auth/login/"

username_from_env = os.getenv("OCEAN_USERNAME")
password_from_env = os.getenv("OCEAN_PASSWORD")

def create_authorization_header(access_token):
    return {"Authorization": f"Bearer {access_token}"}

def get_access_token(username, password):
    url = f"{AUTH_ENDPOINT}?username={username}&password={password}"
    response = requests.post(url)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        print(f"Access token successfully generated {access_token[0:10]}...({len(access_token)-10} truncated).")
        return access_token
    else:
        print(f"Error logging in: {response.status_code} - {response.text}")
        return None

# Output directory (change as needed)
DOWNLOAD_DIR = "downloads"

def fetch_selections(recording_id, access_token):
    """Fetch all selections for a given recording ID."""
    access_token = get_access_token(username_from_env, password_from_env)
    url = f"{SELECTIONS_ENDPOINT}?recording_id={recording_id}"
    response = requests.get(url, headers=create_authorization_header(access_token))

    if response.status_code == 200:
        return response.json()  # Expecting a list of selections
    else:
        print(f"Error fetching selections: {response.status_code} - {response.text}")
        return []

def download_species(species_id, access_token):
    """Fetch all encounters for a given species"""
    access_token = get_access_token(username_from_env, password_from_env)
    url = f"{ENCOUNTERS_ENDPOINT}?species_id={species_id}"
    response = requests.get(url, stream=True, headers=create_authorization_header(access_token)) 
    encounter_list = []
    for x in range(0,len(response.json()) -1):
        encounter_list.append(response.json()[x]['id'])

    if response.status_code == 200:
        return encounter_list
    else:
        print(f"Error fetching selections: {response.status_code} - {response.text}")
        return []

def download_recording(encounter_id, access_token):
    """Fetch all recordings for a given encounter"""
    access_token = get_access_token(username_from_env, password_from_env)
    url = f"{RECORDINGS_ENDPOINT}?encounter_id={encounter_id}"
    response = requests.get(url, stream=True, headers=create_authorization_header(access_token))
    recording_list = []
    for x in range(0,len(response.json()) -1):
        recording_list.append(response.json()[x]['id'])

    if response.status_code == 200:
        return recording_list
    else:
        print(f"Error fetching selections: {response.status_code} - {response.text}")
        return []


def download_selection_file(selection_file_id, access_token, species_id):
    """Download a selection file and save it with the given filename."""
    access_token = get_access_token(username_from_env, password_from_env)
    url = f"{FILES_ENDPOINT}?id={selection_file_id}"
    response = requests.get(url, stream=True, headers=create_authorization_header(access_token))  # Stream for large files
    
    content_type = response.headers.get("Content-Type", "")
    content_disposition = response.headers.get("Content-Disposition", "")
    
    if response.status_code == 200 and "audio/wav" in content_type and "filename=" in content_disposition:
        # Extract filename from the Content-Disposition header


        filename = f"{species_id}_" + content_disposition.split("filename=")[1].strip().strip('"')
        
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(file_path, "wb") as file:
            
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Error downloading file {selection_file_id}: {response.status_code}")

def download_spectrogram_file(selection_id, access_token, species_id):
    url = f"{SPECTROGRAM_ENDPOINT}?selection_id={selection_id}"
    response = requests.get(url, stream=True, headers=create_authorization_header(access_token))  # Stream for large files
    content_type = response.headers.get("Content-Type", "")
    content_disposition = response.headers.get("Content-Disposition", "")
    if response.status_code == 200 and "image/png" in content_type and "filename=" in content_disposition:
        # Extract filename from the Content-Disposition header
        filename = content_disposition.split("filename=")[1].strip().strip('"')
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Error downloading file {selection_id}: {response.status_code}")


def main(recording_id):
    """Download all selections and spectrograms in a recording.
    Make sure OCEAN_USERNAME and OCEAN_PASSWORD are set as global environment variables.
    """

    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    species_ids = ["3ebfce8d-769b-11ef-9a56-0050568e393c","3ebfcfab-769b-11ef-9a56-0050568e393c"]
    access_token = get_access_token(username_from_env, password_from_env)
    for species_id in species_ids:
        count = 0
        # Fetch species from an encounter
        encounter_ids = download_species(species_id,access_token)

        for encounter_id in encounter_ids:
            # Fetch recording from an encounter
            recording_ids = download_recording(encounter_id,access_token)
            for recording_id in recording_ids:
                # Fetch selections from recording
                selections = fetch_selections(recording_id, access_token)
                # Process each selection into files
                for selection in selections:
                    selection_file_id = selection.get("selection_file_id")
                    if selection_file_id:
                        count += 1
                        download_selection_file(selection_file_id, access_token, species_id)
                        #download_spectrogram_file(selection["id"], access_token, species_id)
                    else:
                        print(f"Skipping selection with missing file ID: {selection}")
        print(count)
if __name__ == "__main__":
    
    main("0150032b-bded-11ef-90ba-0050568e393c")
