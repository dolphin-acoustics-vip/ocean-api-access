# ocean-api-access

A small, self-contained example of how to access the OCEAN API from Python:
log in, browse metadata (encounters, recordings, selections, species) and
download the audio file and spectrogram of a selection.

The API is served by the
[database-management-system](https://github.com/dolphin-acoustics-vip/database-management-system);
the interactive (Swagger) documentation is available on the server at
`https://research.st-andrews.ac.uk/ocean/api/`.

## Setup

1. Install Python 3.8+ and the dependency:

   ```
   pip install -r requirements.txt
   ```

2. Set your credentials as
   [environment variables](https://www3.ntu.edu.sg/home/ehchua/programming/howto/Environment_Variables.html):

   | Variable         | Value                                                                 |
   |------------------|-----------------------------------------------------------------------|
   | `OCEAN_USERNAME` | Your full email address, including `@st-andrews.ac.uk`.              |
   | `OCEAN_PASSWORD` | Your **API password**, provided by your administrator. This is not your normal login password. |

   Linux / macOS: `export OCEAN_USERNAME="you@st-andrews.ac.uk"`
   Windows (PowerShell): `$env:OCEAN_USERNAME = "you@st-andrews.ac.uk"`

## Jumpstart: your first script

1. Copy `starter.py` (e.g. `cp starter.py my_script.py`).
2. Edit the `CONFIG` section at the top, e.g. filter encounters by `location` or `project`.
3. Run it: `python3 my_script.py`.

It prints the encounters you can access, then downloads the audio and
spectrogram of the first few selections into `downloads/`.

For anything beyond that, use the client directly:

```python
from ocean_client import OceanClient

client = OceanClient()                       # reads OCEAN_USERNAME / OCEAN_PASSWORD
encounters = client.encounters(location="Hawaii")
recordings = client.recordings(encounter_id=encounters[0]["id"])
selections = client.selections(recording_id=recordings[0]["id"])
client.download_audio(selections[0], "downloads")
client.download_spectrogram(selections[0], "downloads")
```

`print()` any returned item to see its fields. The client logs in for you,
logs in again when the 15-minute token expires, and fetches every page.

## Running the demo

```
python3 main.py
```

With no arguments the demo needs no IDs. It logs in, walks
encounter → recording → selection until it finds a selection with an audio file,
and downloads that selection's `.wav` and spectrogram `.png` into `downloads/`.

Other modes, if you already know an ID:

```
python3 main.py --encounter-id <ID>    # print an encounter and its recordings
python3 main.py --recording-id <ID>    # download every selection + spectrogram in a recording
```

## How the API works

### Authentication

`POST /auth/login/?username=...&password=...` returns `{"access_token": "<JWT>"}`.
Send it on every other request as the header `Authorization: Bearer <token>`.
**Tokens expire after 15 minutes**; log in again if you get a `401`.

### Endpoints

All paths are relative to `https://research.st-andrews.ac.uk/ocean/api`.

| Endpoint                         | Returns            | Filters (query parameters)                                              |
|----------------------------------|--------------------|-------------------------------------------------------------------------|
| `GET /metadata/encounters/`      | JSON list          | `id`, `encounter_name`, `location`, `project`, `species_id`             |
| `GET /metadata/recordings/`      | JSON list          | `id`, `encounter_id`, `start_time` (ISO 8601)                           |
| `GET /metadata/selections/`      | JSON list          | `id`, `recording_id`, `selection_number`                                |
| `GET /metadata/species/`         | JSON list          | `id`, `scientific_name`, `common_name`, `genus_name`                    |
| `GET /filespace/file/?id=`       | `audio/wav` file   | `id` (required) – a selection's `selection_file_id`                     |
| `GET /filespace/spectrogram/?selection_id=` | `image/png` file | `selection_id` (required)                                     |

The metadata endpoints are **paginated**: use `page` (default 1) and
`per_page` (default 50). Keep requesting pages until one returns fewer than
`per_page` items.

The data model is a hierarchy; each level links to its parent by ID:

```
species ──< encounter ──< recording ──< selection ──> audio file (selection_file_id)
                                            └──────> spectrogram (selection id)
```

Errors are returned as JSON `{"message": ...}` with status `400` (bad request,
e.g. wrong password), `401` (missing/expired token) or `404` (not found).

### Code overview

| File               | Purpose                                                              |
|--------------------|----------------------------------------------------------------------|
| `ocean_client.py`  | The reusable `OceanClient`: login, token refresh, paging, downloads. |
| `starter.py`       | Template to copy and edit for your own scripts.                      |
| `main.py`          | The no-argument demo and `--encounter-id` / `--recording-id` modes.  |

`OceanClient` methods:

| Method                                                    | Purpose                              |
|-----------------------------------------------------------|--------------------------------------|
| `encounters(**filters)`, `recordings(...)`, `selections(...)`, `species(...)` | List metadata (all pages); filters as in the table above. |
| `download_audio(selection, directory)`                    | Save a selection's `.wav`.           |
| `download_spectrogram(selection, directory)`              | Save a selection's `.png`.           |
| `login()`                                                 | Force a new token (normally automatic). |
