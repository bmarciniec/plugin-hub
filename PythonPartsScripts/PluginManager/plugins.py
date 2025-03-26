"""Module containing the classes for storing and managing ALLPLAN plugins."""
from __future__ import annotations

import json
import warnings

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import cast
from uuid import UUID

import NemAll_Python_Utility as AllplanUtil
import requests

from BuildingElement import BuildingElement
from ControlPropertiesUtil import ControlPropertiesUtil
from FileNameService import FileNameService
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from ParameterProperty import ParameterProperty

from . import config
from .developers import Developer, DeveloperIndex
from .installer import AllepInstaller
from .releases import Release, Releases
from .util import date_to_str, delete_folder, make_step_progress_bar, remove_directory
from .yaml_models import sanitize_strings


class PluginsCollection:
    """Representation of a collection of ALLPLAN plugins."""

    def __init__(self, plugins: dict[UUID, Plugin] | None = None):
        """Initialization of the PluginsCollection.

        Args:
            plugins (dict[UUID, Plugin]): Dictionary with the
                plugins as values and their UUIDs as keys.
        """
        self._plugins = plugins if plugins is not None else dict()
        """Dictionary with the plugins as values and their UUIDs as keys."""

        self._sorted_uuids: list[UUID] = []
        """List of UUIDs in the alphabetical order of the plugins."""

        try:
            self.developers = DeveloperIndex.from_github()
        except requests.exceptions.ConnectionError:
            self.developers = DeveloperIndex()


    def append(self, new_plugin: Plugin):
        """Append a new plugin to the collection.

        If the plugin is already in the collection, the new plugin is fetched into the existing one.

        Args:
            new_plugin (Plugin): Plugin to append.
        """
        if new_plugin.uuid in self._plugins:
            self._plugins[new_plugin.uuid].fetch(new_plugin)
        else:
            self._plugins[new_plugin.uuid] = new_plugin

        self._sort_plugins()

    def get_plugins_from_github(self):
        """ Get the plugins from the allplan-plugins.json file in the GitHub repository."""

        response = requests.get(config.EXTENSIONS_URL, timeout=10, headers=config.GITHUB_API_HEADERS)
        response.raise_for_status()
        plugin_list = response.json()

        for plugin_dict in plugin_list:
            # If the developer is not in the developer index, skip the plugin
            try:
                plugin_dict["developer"] = self.developers[plugin_dict["developer"]]
            except KeyError:
                continue

            self.append(Plugin.from_github_data(plugin_dict))

        self._sort_plugins()

    def get_installed_plugins(self):
        """Get the plugins installed in Allplan.

        This method reads the manifests.json file from all the locations where plugins can be installed (usr, std, etc)
        and adds the plugins to the collection.
        """

        for location in InstallLocations:
            manifests_path = Path(FileNameService.get_global_standard_path(f"{location}\\AllepPlugins\\manifests.json"))

            if not manifests_path.exists():
                continue

            with open(manifests_path, encoding = "UTF-8") as file:
                manifest = json.load(file)

            for plugin_data in manifest["plugins"]:
                self.append(Plugin.from_manifest_data(location, plugin_data))

    def update_plugins_overview_on_palette(self, build_ele: BuildingElement):
        """Populate the building element with the plugin information.

        Args:
            build_ele (BuildingElement): Building element to populate.
            only_status (bool): If True, only the status of the plugins is updated, otherwise all the plugin information is updated.
        """

        # fill the palette with installed plugins
        build_ele.InstalledPluginNames.value         = [plgn.name for plgn in self if plgn.status != PluginStatus.NOT_INSTALLED]
        build_ele.InstalledPluginDescriptions.value  = [plgn.description for plgn in self if plgn.status != PluginStatus.NOT_INSTALLED]

        # fill the palette with not installed plugins
        build_ele.AvailablePluginNames.value         = [plgn.name for plgn in self if plgn.status == PluginStatus.NOT_INSTALLED]
        build_ele.AvailablePluginDescriptions.value  = [plgn.description for plgn in self if plgn.status == PluginStatus.NOT_INSTALLED]

        # palette does not show up if one of the lists is empty
        for prop_name in ("InstalledPluginNames", "InstalledPluginDescriptions", "AvailablePluginNames", "AvailablePluginDescriptions"):
            build_ele.get_existing_property(prop_name).value = build_ele.get_existing_property(prop_name).value or ["EMPTY"]


    def clean_up(self):
        """Remove the plugins from the collection, that are not installed and don't have a GitHub repository."""
        self._plugins = {uuid: plugin for uuid, plugin in self._plugins.items() if plugin.status != PluginStatus.NOT_INSTALLED or plugin.has_github}
        self._sort_plugins()

    def _sort_plugins(self):
        """Sort the plugins by their names."""
        self._sorted_uuids = sorted(self._plugins, key=lambda uuid: self._plugins[uuid].name)

    def __getitem__(self, key: UUID | int) -> Plugin:   # pylint: disable=W9015,W9011
        """Get a plugin by its UUID."""
        if isinstance(key, int):
            return self._plugins[self._sorted_uuids[key]]
        return self._plugins[key]

    def __iter__(self):         # pylint: disable=W9011,W9012
        """Iterate over the plugins in alphabetical order of the plugin names."""
        return iter(self._plugins[uuid] for uuid in self._sorted_uuids)

    def __len__(self) -> int:   # pylint: disable=W9015,W9011
        """Get the number of plugins."""
        return len(self._plugins)

    def __repr__(self):         # pylint: disable=W9011,W9012
        """Representation of the PluginsCollection."""
        return f"{self.__class__.__name__}({self._plugins})"


class PluginStatus(IntEnum):
    """Enum to represent the status of an plugin. Used to show correct UI elements in the PythonPart palette."""

    NOT_INSTALLED = 0
    """Plugin is not installed."""

    INSTALLED = 1
    """Plugin is installed, but unknown whether the latest version."""

    UPDATE_AVAILABLE = 2
    """Plugin is installed, but an update is available."""

    UP_TO_DATE = 3
    """Plugin is installed and up to date."""


class InstallLocations(StrEnum):
    """Enum to represent the possible locations, where plugins can be installed."""

    ETC = "etc"
    """Plugins installed in the etc folder."""

    STD = "std"
    """Plugins installed in the std folder."""

    USR = "usr"
    """Plugins installed in the usr folder."""


@dataclass
class Plugin:
    """Dataclass to represent an ALLPLAN plugin.

    Attributes:
        uuid (UUID): UUID of the plugin.
        name (str): Name of the plugin.
        description (str): Short description of the plugin.
        github (dict): Dictionary with the GitHub repository information.
    """
    # Required attributes
    uuid              : UUID
    name              : str
    developer         : Developer

    # Optional attributes
    description       : str                     = ""
    github            : dict[str,str] | None             = field(default=None)
    installed_date    : datetime | None         = field(default=None)
    installed_files   : set[Path]               = field(default_factory=set)
    installed_version : Version | None          = field(default=None)
    location          : InstallLocations | None = field(default=None)
    local_file        : Path | None             = field(default=None)
    compatibility     : SpecifierSet | None     = field(default=None)

    # Internal attributes
    _last_version_check : datetime | None     = field(init=False, default=None, repr=False, compare=False)
    _releases           : Releases            = field(init=False, default_factory=Releases)

    def __post_init__(self):
        """Post initialization of the Plugin object."""

        # convert installed files from the manifest file to Path and fix some issues, they can have
        # TODO: when the issue with paths in manifest files is fixed, move thi spart to from_manifest_data
        if len(self.installed_files) > 0 and any(isinstance(item, str) for item in self.installed_files):
            self.installed_files = set(self.installed_files)
            installed_files = cast(set[str], set(self.installed_files))
            self.installed_files.clear()

            for path in installed_files:
                if path.startswith("Usr"):
                    parts = path.split("\\")
                    parts.pop(1)
                    path = "\\".join(parts)

                absolute_path = Path(FileNameService.get_global_standard_path(path))

                if absolute_path.exists() and absolute_path.is_file():
                    self.installed_files.add(absolute_path)

    def check_releases(self, progress_bar: AllplanUtil.ProgressBar | None = None):
        """Get the available releases from GitHub

        Args:
            progress_bar: Instance of progress_bar. When provided, it will be increased by 10 steps.
        """
        if not self.has_github:
            return

        if progress_bar is not None:
            progress_bar.SetTitle(f"Checking {self.name}...")

        self._releases.get_from_github(**self.github)

        if progress_bar is not None:
            progress_bar.MakeStep(19)

        self._last_version_check = datetime.now()

    @classmethod
    def from_github_data(cls, data: dict) -> Plugin:
        """Create a plugin based on an entry in the allplan-extensions.json in the plugin hub.

        Args:
            data (dict): Dictionary with the plugin data.

        Returns:
            Plugin: Plugin object created from the data.
        """
        compatibility = SpecifierSet(data["compatibility"]) if data.get("compatibility") else None
        return cls(
            uuid          = UUID(data["uuid"]),
            name          = data["name"],
            developer     = data["developer"],
            description   = data["description"],
            github        = data["github"],
            compatibility = compatibility
        )

    @classmethod
    def from_manifest_data(cls, location: InstallLocations, data: dict) -> Plugin:
        """Create a plugin based on entry in the manifests.json file.

        Args:
            data (dict): Dictionary with the plugin data from the manifests.json file.
            location (InstallLocations): Location where the plugin is installed.

        Returns:
            Plugin: Plugin object created from the data.
        """
        return cls(
            uuid              = UUID(data["UUID"]),
            name              = data["pluginName"],
            developer         = Developer(data["developerName"]),
            installed_date    = datetime.fromisoformat(data["createdOn"]),
            installed_version = Version(data["version"]),
            installed_files   = data["filesCopied"] + [data["ACTBFile"], data["NPDFile"]],
            location          = location
        )

    def install(self, progress_bar: AllplanUtil.ProgressBar | None = None, version: Version | None = None):
        """Install the plugin from GitHub

        Args:
            progress_bar: Instance of progress_bar. When provided, it will be increased by 190 steps.

        Raises:
            RuntimeError: when trying to install a plugin with no release compatible with this ALLPLAN version
        """

        if not self._releases:
            self._releases.get_from_github(**self.github)

        if version is not None:
            release_to_install = self.releases.get_release_by_version(version)
        else:
            release_to_install = self.latest_compatible_release

        if release_to_install is None:
            raise RuntimeError("Cannot install this plugin, as no release compatible with this Allplan version was found")

        installer = AllepInstaller(release_to_install.allep_package)
        installer.download_and_install_package(progress_bar)

        self.installed_version = release_to_install.version
        self.installed_date    = datetime.now()

    def fetch(self, another_plugin: Plugin):
        """Fetch the attributes of another plugin.

        Args:
            another_plugin (Plugin): Plugin to fetch the attributes from.
        """
        fields_to_update = self.__dataclass_fields__.keys()

        for fld in fields_to_update:
            # if this plugin is registered on github, some data should remain unchanged
            if fld == "developer" and self.has_github:
                continue

            # otherwise, update all fields
            if getattr(another_plugin, fld):
                setattr(self, fld, getattr(another_plugin, fld))

    def update_plugin_details_on_palette(self, build_ele: BuildingElement, only_status: bool = False):
        """Fill the palette with the plugin information.

        Args:
            build_ele: Building element to populate.
            control_props_util: Control properties utility to alter the visibility of the palette elements.
        """
        build_ele.PluginStatus.value = self.status
        build_ele.PluginHasGitHub.value = self.has_github

        if only_status:
            return

        _, global_str_table = build_ele.get_string_tables()
        location_texts = {
            "std": global_str_table.get_string("e_OFFICE", "Office"),
            "usr": global_str_table.get_string("e_PRIVAT", "Private"),
            "etc": global_str_table.get_string("e_STANDARD", "Standard"),
        }

        # fill the palette with the plugin information
        build_ele.PluginUUID.value        = str(self.uuid)
        build_ele.PluginName.value        = self.name
        build_ele.InstallDate.value       = date_to_str(self.installed_date) if self.installed_date else ""
        build_ele.InstalledVersion.value  = str(self.installed_version) if self.installed_version else ""
        build_ele.InstallLocation.value   = location_texts[self.location] if self.location else ""

        # fill the developer information
        build_ele.DeveloperName.value          = self.developer.name or self.developer.id
        build_ele.DeveloperSupportEmail.value  = self.developer.support.email if self.developer.support else ""
        build_ele.DeveloperAddress.value       = self.developer.address.full_address if self.developer.address else ""
        build_ele.DeveloperHomepage.value      = self.developer.homepage.strip("https://")

    def uninstall(self, progress_bar: AllplanUtil.ProgressBar | None = None):
        """ Uninstall the plugin.

        Removes the installed files and entried in the manifests.json file.

        Args:
            progress_bar: Instance of progress_bar. When provided, it will be increased by 70 steps.

        Warns:
            ResourceWarning: If a certain file is being used by another process and cannot be removed.
        """

        if self.status == PluginStatus.NOT_INSTALLED:
            return

        folder_path   = Path(FileNameService.get_global_standard_path(f"{self.location}\\"))   # type: ignore

        # Remove files

        make_step_progress_bar(40, "Removing files", progress_bar)

        while self.installed_files:
            if not (file := self.installed_files.pop()):
                continue

            try:
                file.unlink()
            except PermissionError as e:
                warnings.warn(f"File {file} is being used by another process and won't be removed. {e}", ResourceWarning)

        for folder in ("Library", "PythonPartsScripts", "PythonPartsActionbar"):
            plugin_directory = folder_path / folder / "AllepPlugins" / sanitize_strings(self.developer.name) / sanitize_strings(self.name)
            make_step_progress_bar(10, "Removing directories", progress_bar)
            remove_directory(str(plugin_directory))
            delete_folder(str(plugin_directory.parent))

        # Update manifest file

        make_step_progress_bar(10, "Updating manifest files", progress_bar)

        file_path = folder_path / "AllepPlugins" / "manifests.json"

        if not file_path.exists():
            return

        result  = []

        with open(file_path, encoding = "UTF-8") as file:
            manifest_data = json.load(file)

            for _, plugin in enumerate(manifest_data.get("plugins", [])):
                if plugin["UUID"] == str(self.uuid):
                    continue

                result.append(plugin)

        manifest_data["plugins"] = result

        with open(file_path, "w", encoding="UTF-8") as file:
            json.dump(manifest_data, file)

        self.installed_date = None
        self.installed_version = None
        self.location = None

        make_step_progress_bar(10, "Completed", progress_bar)

    def fill_versions_combo_box(self, param: ParameterProperty, control_props_util: ControlPropertiesUtil):
        """Fill the combo box with the available versions of the plugin.

        Args:
            param: Parameter property representing the combobox to fill.
            control_props_util: Control properties utility to alter the combobox entries.
        """
        combo_box_entries = []
        selected_entry = ""
        sorted_releases = sorted(list(self.releases), key = lambda x: x.version, reverse=True)

        for release in sorted_releases:
            combo_box_entry = f"{str(release.version)} ({release.published_ago}"

            if self.latest_compatible_release is not None and release.version == self.latest_compatible_release.version:
                combo_box_entry += ", latest"

            combo_box_entry += ")"

            if self.installed_version and release.version == self.installed_version:
                selected_entry = combo_box_entry

            combo_box_entries.append(combo_box_entry)

        control_props_util.set_value_list(param.name, "|".join(combo_box_entries))
        param.value = selected_entry

    @property
    def has_github(self) -> bool:
        """Check if the plugin has a GitHub repository attached.

        Returns:
            bool: True if the plugin has a GitHub repository attached, False otherwise.
        """
        return self.github is not None

    @property
    def is_on_actionbar(self) -> bool:
        """Check if the plugin is integrated on the Actionbar.

        Returns:
            bool: True if the plugin is integrated to the Actionbar, False otherwise.
        """
        if self.status == PluginStatus.NOT_INSTALLED:
            return False

        return any(file.name.lower().endswith(".actb") for file in self.installed_files)

    @property
    def latest_compatible_release(self) -> Release | None:
        """Get the latest version of the plugin, that is compatible with the current ALLPLAN version

        If no compatibility information is provided, the release marked in github as latest is returned.

        Returns:
            Version: Latest version of the plugin. None if no compatible version is found.

        Raises:
            RuntimeError: If the plugin does not have a GitHub repository attached
        """
        if not self.has_github:
            raise RuntimeError("Cannot get the latest version of the plugin because there is no GitHub repository attached.")

        if not self._releases:
            raise RuntimeError("No data about available releases. Call check_releases() first!")

        # when no compatibility is set, get the release marked in GitHub as latest
        if not self.compatibility:
            return self._releases.get_latest(self.github["owner"], self.github["repo"])

        # get the latest release that is compatible with the current version of Allplan
        return self.releases.get_latest_matching(self.compatibility)

    @property
    def releases(self) -> Releases:
        """Get a subset of all releases (also pre-releases), that are compatible with the current ALLPLAN version

        Returns:
            Releases: Releases of the plugin.
        """
        if self.has_github and not self._releases:
            raise RuntimeError("No data about available releases. Call check_releases() first!")

        if self.compatibility is not None:
            return self._releases.get_matching(self.compatibility, True)

        return self._releases

    @property
    def status(self) -> PluginStatus:
        """Get the status of the plugin.

        Returns:
            PluginStatus: Status of the plugin.
        """
        if self.installed_version is None:
            return PluginStatus.NOT_INSTALLED

        if not self.has_github or not self._releases:
            return PluginStatus.INSTALLED

        if (latest_compatible := self.latest_compatible_release) is None:
            return PluginStatus.INSTALLED

        if self.installed_version < latest_compatible.version:
            return PluginStatus.UPDATE_AVAILABLE

        return PluginStatus.UP_TO_DATE
