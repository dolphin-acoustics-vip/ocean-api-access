import os
import requests

# API URLs
BASE_URL = "https://rescomp-test-2.st-andrews.ac.uk/ocean/api"
SELECTIONS_ENDPOINT = f"{BASE_URL}/metadata/selections/"
ENCOUNTERS_ENDPOINT = f"{BASE_URL}/metadata/encounters/"
FILES_ENDPOINT = f"{BASE_URL}/filespace/file/"
SPECTROGRAM_ENDPOINT = f"{BASE_URL}/filespace/spectrogram/"
AUTH_ENDPOINT = f"{BASE_URL}/auth/login/"

def create_authorization_header(access_token):
    return {"Authorization": f"Bearer {access_token}"}

def get_access_token(username, password):
    url = f"{AUTH_ENDPOINT}?username={username}&password={password}"
    print(f"Fetching access token... {url}")
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
    url = f"{SELECTIONS_ENDPOINT}?recording_id={recording_id}"
    response = requests.get(url, headers=create_authorization_header(access_token))

    if response.status_code == 200:
        return response.json()  # Expecting a list of selections
    else:
        print(f"Error fetching selections: {response.status_code} - {response.text}")
        return []

def download_encounters(encounter_id, access_token):
    url = f"{ENCOUNTERS_ENDPOINT}?id={encounter_id}"
    response = requests.get(url, stream=True, headers=create_authorization_header(access_token))  # Stream for large files

    content_type = response.headers.get("Content-Type", "")
    content_disposition = response.headers.get("Content-Disposition", "")
    encounter_content = response.json()[0]['species_id']
    
    if response.status_code == 200 and "application/json" in content_type and "filename=" in content_disposition:
        # Extract filename from the Content-Disposition header
        filename = content_disposition.split("filename=")[1].strip().strip('"')
        
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(file_path, "wb") as file:
            
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Error downloading file {encounter_id}: {response.status_code}")

def download_selection_file(selection_file_id, access_token):
    """Download a selection file and save it with the given filename."""
    url = f"{FILES_ENDPOINT}?id={selection_file_id}"
    response = requests.get(url, stream=True, headers=create_authorization_header(access_token))  # Stream for large files
    
    content_type = response.headers.get("Content-Type", "")
    content_disposition = response.headers.get("Content-Disposition", "")
    
    if response.status_code == 200 and "audio/wav" in content_type and "filename=" in content_disposition:
        # Extract filename from the Content-Disposition header
        print(content_disposition)
        filename = content_disposition.split("filename=")[1].strip().strip('"')
        
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(file_path, "wb") as file:
            
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Error downloading file {selection_file_id}: {response.status_code}, {response.text}")

def download_spectrogram_file(selection_id, access_token):
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
        print(f"Error downloading spectrogram {selection_id}: {response.status_code}, {response.text}")


def main(recording_id):
    """Download all selections and spectrograms in a recording.
    Make sure OCEAN_USERNAME and OCEAN_PASSWORD are set as global environment variables.
    """
    encounter_id = "003b28ca-861d-4348-97ca-aa378b08cc6b"

    username_from_env = os.getenv("OCEAN_USERNAME")
    password_from_env = os.getenv("OCEAN_PASSWORD")

    access_token = get_access_token(username_from_env, password_from_env)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Fetch selections
    selections = fetch_selections(recording_id, access_token)
    print(f"Found {len(selections)} selections for recording {recording_id}")

    # Process each selection
    for selection in selections:
        selection_file_id = selection.get("selection_file_id")
        if selection_file_id:
            #download_selection_file(selection_file_id, access_token)
            download_encounters(encounter_id,access_token)
            #download_spectrogram_file(selection["id"], access_token)
        else:
            print(f"Skipping selection with missing file ID: {selection}")


if __name__ == "__main__":
    main("0150032b-bded-11ef-90ba-0050568e393c")
