"""Module to represent an ALLEP package attached to a plugin."""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import NemAll_Python_Utility as AllplanUtil
import requests

from .util import make_step_progress_bar


@dataclass
class AllepPackage:
    """Dataclass to represent an ALLEP package attached to a plugin.

    Attributes:
        name (str): Name of the ALLEP package.
        size (int): Size of the ALLEP package in bytes.
        url (str): URL to the .allep file. Empty if the file is local.
        local_path (Path): Local path to the .allep file.
    """
    name:       str
    size:       int       = field(default=0)
    url:        str|None  = field(default=None)
    local_path: Path|None = field(default=None)

    @property
    def is_local(self) -> bool:
        """Check if the path is a local path or a URL.

        Returns:
            bool: True if the path is a local path, False if it's a URL.
        """
        parsed = urlparse(self.url)
        return not parsed.scheme in ('http', 'https')

    def download(self, save_directory: Path, progress_bar: AllplanUtil.ProgressBar | None = None) -> bool:
        """Download the ALLEP package from the URL.

        Args:
            save_directory (Path): Path to the directory, where to save the ALLEP package.
            progress_bar (AllplanUtil.ProgressBar | None): Progress bar to update. If provided, it will be increased by max 100 steps.

        Returns:
            bool: True if the download was done, False if the file was already downloaded.

        Raises:
            FileNotFoundError: If the destination directory does not exist.
            requests.HTTPError: If the request to the URL fails.
        """
        if self.downloaded:
            return False

        if not save_directory.exists():
            raise FileNotFoundError(f"Directory {save_directory} does not exist.")

        save_path = save_directory / self.name

        # Delete the file if it already exists
        if save_path.exists():
            save_path.unlink()

        response = requests.get(self.url, stream=True, timeout=10)
        response.raise_for_status()

        chunk_size = 8192
        step_size = 100 // -(- self.size // chunk_size)

        with open(save_path, 'wb') as file:
            downloaded_size = 0

            for chunk in response.iter_content(chunk_size):
                file.write(chunk)
                make_step_progress_bar(step_size, "Downloading the plugin", progress_bar)
                downloaded_size += len(chunk)

            self.local_path = save_path

        return True

    def delete_local_file(self):
        """Delete the local ALLEP file."""
        if self.local_path and self.local_path.exists():
            self.local_path.unlink()
            self.local_path = None

    @property
    def downloaded(self):
        """Check if the ALLEP package has been downloaded.

        Returns:
            bool: True if the ALLEP package has been downloaded, False otherwise.
        """
        return bool(self.local_path)
