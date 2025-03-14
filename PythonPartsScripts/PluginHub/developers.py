"""This module contains classes to represent developers and an index of developers."""
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests

from . import config


@dataclass
class Address:
    """Class for the address of a developer."""
    street: str
    city: str
    zip: str
    country: str

@dataclass
class Support:
    """Class for the support contact information of a developer."""
    email: str
    languages: list[str]

@dataclass
class Developer:
    """Class for a developer."""
    id: str
    name: str
    address: Address
    home_page: str
    support: Support
    github: str

class DeveloperIndex:
    """Class for an index of developers."""

    def __init__(self):
        """Initialize an empty developer index."""
        self._developers = {}

    def get_developers_from_github(self, branch: str):
        """ Get the plugins from the allplan-plugins.json file in the GitHub repository.

        Args:
            branch: Git branch to get the plugins from.
        """

        url = f'https://raw.githubusercontent.com/{config.PluginHubRepo.OWNER}/{config.PluginHubRepo.REPO}/{branch}/plugin-developers.json'

        response = requests.get(url, timeout=10, headers=config.GITHUB_API_HEADERS)
        response.raise_for_status()
        developer_list = response.json()

        for developer_dict in developer_list:
            self.add(Developer(**developer_dict))


    def add(self, developer: Developer):
        """Add a developer to the index.

        Args:
            developer: New developer to add to the index.
        """
        if developer.id in self._developers:
            return
        self._developers[developer.id] = developer

    def __iter__(self) -> Iterator[Developer]:
        """Iterate over all developers in the index."""
        return iter(self._developers.values())

    def __getitem__(self, key:str) -> Developer:
        """Get a developer by its ID."""
        try:
            return self._developers[key]
        except KeyError:
            raise KeyError(f"Developer with ID {key} not found.") from None
