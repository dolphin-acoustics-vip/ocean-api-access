"""A small client for the OCEAN API.

Import it from your own scripts:

    from ocean_client import OceanClient

    client = OceanClient()                      # reads OCEAN_USERNAME / OCEAN_PASSWORD
    for encounter in client.encounters(location="Hawaii"):
        print(encounter)

The client logs in on first use and logs in again automatically when the
15-minute token expires. List methods return plain lists of dicts and fetch
every page for you.
"""
import os
import re

import requests

BASE_URL = "https://research.st-andrews.ac.uk/ocean/api"
PER_PAGE = 50   # server default page size
TIMEOUT = 30    # seconds


class ApiError(Exception):
    """Raised when the API returns an error or credentials are missing."""


class OceanClient:
    def __init__(self, username=None, password=None, base_url=BASE_URL):
        self.username = username or os.getenv("OCEAN_USERNAME")
        self.password = password or os.getenv("OCEAN_PASSWORD")
        if not self.username or not self.password:
            raise ApiError("Set the OCEAN_USERNAME and OCEAN_PASSWORD environment variables first.")
        self.base_url = base_url.rstrip("/")
        self._token = None

    # -- authentication ----------------------------------------------------

    def login(self):
        """Fetch a fresh access token (valid for 15 minutes)."""
        # The server reads the credentials from the query string of a POST;
        # `params` URL-encodes them correctly.
        response = requests.post(
            f"{self.base_url}/auth/login/",
            params={"username": self.username, "password": self.password},
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            raise ApiError(f"Login failed: {response.status_code} - {response.text}")
        self._token = response.json()["access_token"]

    def _get(self, path, stream=False, **params):
        """GET with the auth header; logs in first, and again once if the token expired."""
        if self._token is None:
            self.login()
        for attempt in range(2):
            response = requests.get(
                f"{self.base_url}{path}",
                params=params,
                headers={"Authorization": f"Bearer {self._token}"},
                stream=stream,
                timeout=TIMEOUT,
            )
            if response.status_code == 401 and attempt == 0:
                self.login()
                continue
            break
        if response.status_code != 200:
            raise ApiError(f"GET {path} failed: {response.status_code} - {response.text[:200]}")
        return response

    # -- metadata ----------------------------------------------------------

    def _list(self, path, **filters):
        """Return every item from a paginated metadata endpoint."""
        filters = {k: v for k, v in filters.items() if v is not None}
        results, page = [], 1
        while True:
            items = self._get(path, page=page, per_page=PER_PAGE, **filters).json()
            results.extend(items)
            if len(items) < PER_PAGE:
                return results
            page += 1

    def encounters(self, **filters):
        """Filters: id, encounter_name, location, project, species_id."""
        return self._list("/metadata/encounters/", **filters)

    def recordings(self, **filters):
        """Filters: id, encounter_id, start_time (ISO 8601)."""
        return self._list("/metadata/recordings/", **filters)

    def selections(self, **filters):
        """Filters: id, recording_id, selection_number."""
        return self._list("/metadata/selections/", **filters)

    def species(self, **filters):
        """Filters: id, scientific_name, common_name, genus_name."""
        return self._list("/metadata/species/", **filters)

    # -- files -------------------------------------------------------------

    def _download(self, path, directory, **params):
        """Stream a file into `directory`, named by the server. Returns the file path."""
        os.makedirs(directory, exist_ok=True)
        with self._get(path, stream=True, **params) as response:
            match = re.search(r'filename="?([^";]+)"?', response.headers.get("Content-Disposition", ""))
            if not match:
                raise ApiError(f"GET {path}: response had no filename")
            # basename() stops a path being smuggled into the filename
            file_path = os.path.join(directory, os.path.basename(match.group(1)))
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        return file_path

    def download_audio(self, selection, directory="downloads"):
        """Download a selection's .wav. `selection` is a dict from selections()."""
        return self._download("/filespace/file/", directory, id=selection["selection_file_id"])

    def download_spectrogram(self, selection, directory="downloads"):
        """Download a selection's spectrogram .png."""
        return self._download("/filespace/spectrogram/", directory, selection_id=selection["id"])
