"""This module contains the Release and Releases classes."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Self

import requests

from packaging import specifiers, version

from . import config
from .allep import AllepPackage


@dataclass
class Release:
    """A release of a plugin."""
    version      : version.Version
    published_at : datetime
    url          : str
    is_prerelease: bool
    allep_package: AllepPackage
    latest       : bool = False

    @classmethod
    def from_github_data(cls, data: dict) -> Self:
        """Create a Release object from data from GitHub API.

        Args:
            data: The dictionary with the release data from GitHub.

        Returns:
            A Release object.

        Raises:
            ValueError: If the release does not contain any allep package
        """
        try:
            assets = data["assets"]
        except KeyError as err:
            raise ValueError("No assets found in the release data.") from err

        allep_package = None

        for asset in assets:
            if asset.get("name","").lower().endswith(".allep"):
                allep_package = AllepPackage(
                    name = asset["name"],
                    url = asset["browser_download_url"],
                    size = asset["size"])
                break

        if allep_package is None:
            raise ValueError("No Allep package found in the latest release of this plugin on GitHub.")

        return cls(
            version       = version.parse(data["tag_name"]),
            published_at  = datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%SZ"),
            url           = data["html_url"],
            is_prerelease = data["prerelease"],
            allep_package = allep_package
        )

    @property
    def published_ago(self) -> str:
        """Return string since the release was published.

        Returns:
            A string representing the time since the release was published, like "2 wks ago".
        """
        delta = datetime.now() - self.published_at
        days = delta.days

        if days < 30:
            weeks = days // 7
            return f"{weeks} wk{'s' if weeks != 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} mo ago"
        else:
            years = days // 365
            return f"{years} yr{'s' if years != 1 else ''} ago"

    def __hash__(self) -> int:
        """Return the hash of the release."""
        return hash(self.version)

    def __eq__(self, other: object) -> bool:
        """Check if two Release objects are equal based on their version."""
        if not isinstance(other, Release):
            return NotImplemented
        return self.version == other.version


class Releases:
    """A set of releases of a plugin."""

    def __init__(self, iterable: Iterable[Release] | None = None) -> None:
        """Initialize the set of releases.

        Args:
            iterable: An iterable of Release objects.
        """
        self.__releases = set(iterable) if iterable is not None else set()

    def add(self, release:Release):
        """Add a release to the set of releases.

        Args:
            release: The release to add.

        Raises:
            ValueError: When trying to add something else than a Release object
        """
        if not isinstance(release, Release):
            raise ValueError("Only Release objects can be added to the set of releases.")

        self.__releases.add(release)

    def get_matching(self, specifier: specifiers.SpecifierSet, include_prerelease: bool = False) -> Self:
        """Get all the releases compatible with the given specifier.

        Args:
            specifier: The version specifier to check compatibility with.
            include_prerelease: Whether to include prerelease versions.

        Returns:
            Set of releases compatible with the given specifier.
        """
        is_release_matching = lambda release: specifier.contains(release.version) and (include_prerelease or not release.is_prerelease)
        return self.__class__(filter(is_release_matching, self.__releases))

    def get_latest_matching(self, specifier: specifiers.SpecifierSet) -> Release | None:
        """Get the latest release matching given specifier.

        Prereleases are ignored

        Args:
            specifier: The version specifier match the version with.

        Returns:
            The latest release matching with the given specifier.
        """
        if not (compatible_releases := self.get_matching(specifier)):
            return None
        return max(compatible_releases, key=lambda release: release.version)

    def get_latest(self, owner: str, repo: str) -> Release | None:
        """Get the release marked in GitHub as latest

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.

        Returns:
            The latest release from the set of releases.
        """
        # If there is already a release marked as latest, return it
        if latest_release := next((release for release in self if release.latest), None):
            if latest_release is not None:
                return latest_release

        # Otherwise, get the latest release from GitHub
        latest_release = self._get_latest_from_github(owner, repo)

        # Mark the release as latest and return it
        for release in self:
            if release == latest_release:
                release.latest = True
                return release

        # If the release is not in the set, add it and return it
        self.add(latest_release)
        return latest_release

    def get_from_github(self, owner: str, repo: str):
        """Populate this set with data from GitHub

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"

        response = requests.get(url, timeout=10, headers=config.GITHUB_API_HEADERS)
        response.raise_for_status()
        releases = response.json()

        for release_data in releases:
            self.add(Release.from_github_data(release_data))

    def get_release_by_version(self, version: version.Version) -> Release | None:
        """Get a release by version.

        Args:
            version: The version of the release.

        Returns:
            The release with the given version or None if not found.
        """
        for release in self:
            if release.version == version:
                return release
        return None

    @staticmethod
    def _get_latest_from_github(owner: str, repo: str) -> Release:
        """Send a request to GitHub API to get the latest release of the plugin.

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.

        Returns:
            The latest release of the plugin.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

        response = requests.get(url, timeout=10, headers=config.GITHUB_API_HEADERS)
        response.raise_for_status()
        latest_release = Release.from_github_data(response.json())
        latest_release.latest = True
        return latest_release

    def __iter__(self) -> Iterator[Release]:
        """Return an iterator over the releases."""
        yield from self.__releases

    def __contains__(self, release: Release) -> bool:
        """Check if the set of releases contains the given release."""
        return release in self.__releases

    def __len__(self) -> int:
        """Return the number of releases."""
        return len(self.__releases)