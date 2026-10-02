"""Demonstration of access to the OCEAN API.

The API exposes a hierarchy of metadata -- encounter -> recording -> selection --
plus the audio file and spectrogram image belonging to each selection.

Run with no arguments and the script works from scratch: it logs in, finds the
first selection it has access to, and downloads its audio file and spectrogram
into ./downloads. Set OCEAN_USERNAME and OCEAN_PASSWORD first (see README).

Usage:
    python3 main.py                       # self-contained demo
    python3 main.py --encounter-id ID     # show an encounter and its recordings
    python3 main.py --recording-id ID     # download every selection + spectrogram

To write your own scripts, start from starter.py.
"""
import argparse
import sys

from ocean_client import ApiError, OceanClient

DOWNLOAD_DIR = "downloads"


def run_demo(client, max_encounters=20):
    """Find the first selection available to this user and download its files.

    Walks encounters -> recordings -> selections until it finds a selection with
    an audio file, so no IDs need to be known in advance.
    """
    encounters = client.encounters()[:max_encounters]
    print(f"Searching {len(encounters)} encounter(s).")

    for encounter in encounters:
        for recording in client.recordings(encounter_id=encounter["id"]):
            for selection in client.selections(recording_id=recording["id"]):
                if not selection.get("selection_file_id"):
                    continue
                print(f"Encounter {encounter['id']} / recording {recording['id']} / selection {selection['id']}")
                print("Downloaded:", client.download_audio(selection, DOWNLOAD_DIR))
                print("Downloaded:", client.download_spectrogram(selection, DOWNLOAD_DIR))
                return
    print("No selections with audio files were found for this account.")


def show_encounter(client, encounter_id):
    """Print an encounter and the recordings that belong to it."""
    encounters = client.encounters(id=encounter_id)
    if not encounters:
        print(f"No encounter with id {encounter_id}")
        return
    print("Encounter:", encounters[0])
    recordings = client.recordings(encounter_id=encounter_id)
    print(f"{len(recordings)} recording(s):")
    for recording in recordings:
        print(" ", recording)


def download_recording(client, recording_id):
    """Download the audio file and spectrogram of every selection in a recording."""
    selections = client.selections(recording_id=recording_id)
    print(f"Found {len(selections)} selection(s) in recording {recording_id}")
    for selection in selections:
        if not selection.get("selection_file_id"):
            print(f"Skipping selection with missing file ID: {selection}")
            continue
        print("Downloaded:", client.download_audio(selection, DOWNLOAD_DIR))
        print("Downloaded:", client.download_spectrogram(selection, DOWNLOAD_DIR))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--encounter-id", help="show this encounter and its recordings")
    parser.add_argument("--recording-id", help="download all selections and spectrograms of this recording")
    args = parser.parse_args()

    try:
        client = OceanClient()
        client.login()
        print("Logged in.")
        if args.recording_id:
            download_recording(client, args.recording_id)
        elif args.encounter_id:
            show_encounter(client, args.encounter_id)
        else:
            run_demo(client)
    except ApiError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
