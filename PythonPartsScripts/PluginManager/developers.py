"""This module contains classes to represent developers and an index of developers."""
from collections.abc import Iterator
from dataclasses import dataclass

import requests

from . import config


@dataclass
class Address:
    """Class for the address of a developer."""
    street: str
    city: str
    zip: str
    country: str

    @property
    def full_address(self) -> str:
        """Get the full address as a string."""
        return f"{self.street}, {self.zip} {self.city}, {self.country}"


@dataclass
class Support:
    """Class for the support contact information of a developer."""
    email: str
    languages: list[str]


@dataclass
class Developer:
    """Class for a developer."""
    id       : str
    name     : str            = ""
    address  : Address | None = None
    homepage : str            = ""
    support  : Support | None = None
    github   : str            = ""

    def __post_init__(self):
        """Post-initialization of the developer object."""
        if isinstance(self.address, dict):
            self.address = Address(**self.address)
        if isinstance(self.support, dict):
            self.support = Support(**self.support)


class DeveloperIndex:
    """Class for an index of developers."""

    def __init__(self):
        """Initialize an empty developer index."""
        self._developers = {}

    @classmethod
    def from_github(cls) -> 'DeveloperIndex':
        """Create a DeveloperIndex populated with developers indexed in GitHub.

        Returns:
            DeveloperIndex: Index of developers.
        """
        response = requests.get(config.DEVELOEPERS_URL, timeout=10, headers=config.GITHUB_API_HEADERS)
        response.raise_for_status()
        developer_list = response.json()

        index = cls()
        for developer_dict in developer_list:
            index.add(Developer(**developer_dict))
        return index

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

    def __getitem__(self, key: str) -> Developer:
        """Get a developer by its ID."""
        if key in self._developers:
            return self._developers[key]
        raise KeyError(f"Developer with ID {key} not found.")
