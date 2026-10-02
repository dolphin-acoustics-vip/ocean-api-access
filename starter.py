"""Starter template: copy this file and edit the CONFIG section to get your data.

Prerequisites: pip install -r requirements.txt, and set OCEAN_USERNAME and
OCEAN_PASSWORD (see README).

    python3 starter.py

Step 1 prints what you can access. Step 2 downloads the audio and spectrograms
for the selections you choose. Everything is a plain list of dicts, so print()
an item to see what fields are available.
"""
from ocean_client import OceanClient

# ---- CONFIG: edit these ----------------------------------------------------
ENCOUNTER_FILTERS = {
    # Any of: encounter_name, location, project, species_id, id.
    # Leave empty to see every encounter you can access.
    # "location": "Hawaii",
}
MAX_SELECTIONS = 3          # stop after this many downloads
OUTPUT_DIR = "downloads"
# ----------------------------------------------------------------------------

client = OceanClient()

# Step 1: explore
encounters = client.encounters(**ENCOUNTER_FILTERS)
print(f"{len(encounters)} encounter(s) match.")
if encounters:
    print("Example encounter (these are the fields you can filter and use):")
    print(encounters[0])

# Step 2: download audio + spectrograms
downloaded = 0
for encounter in encounters:
    for recording in client.recordings(encounter_id=encounter["id"]):
        for selection in client.selections(recording_id=recording["id"]):
            if downloaded >= MAX_SELECTIONS:
                raise SystemExit(f"Done: downloaded {downloaded} selection(s) to {OUTPUT_DIR}/")
            if not selection.get("selection_file_id"):
                continue
            print(client.download_audio(selection, OUTPUT_DIR))
            print(client.download_spectrogram(selection, OUTPUT_DIR))
            downloaded += 1

print(f"Done: downloaded {downloaded} selection(s) to {OUTPUT_DIR}/")
