"""Module to copy files from package"""

import json
import os

from datetime import date
from typing import Self
from zipfile import ZipFile

import yaml

from .yaml_models import AppConfig
from .util import update_valid_folders

class CopyFiles(AppConfig):
    """Class to move plugin files to repected directories."""

    tracked_files: list[str] = []
    valid_folders: set[str]  = {"Reports", "VisualScripts"}

    def _get_lib_path(self) -> str:
        """Get path of library folder.

        Returns:
            str: Full path to library folder.
        """

        return f"{self.installation.get_path_function()}Library"

    def _get_std_path(self) -> str:
        """Get path of STD folder.

        Returns:
            str: Full path to STD folder.
        """

        return f"{self.installation.get_path_function()}PythonPartsScripts\\AllepPlugins\\{self.plugin.developer}\\{self.plugin.name}"


    def split_by_target_location(self, path: str) -> str:
        """ Split path by target location

        Args:
            path : Full path of the location.

        Returns :
            str : Path split by installation folder.
        """

        return self.installation.target_location + path.split(self.installation.target_location)[1]


    def _make_directory(self, path: str) -> str:
        """Make directory and return its full path

        Args:
            path: path of the directory.

        Returns:
            str: Full path of the newily created folder.
        """

        os.makedirs(path, exist_ok = True)
        return path

    def get_directories(self, package: ZipFile) -> set:
        """Get directories in Archive.

        Args:
            package: Location of the Archive

        Returns:
            set: List of directories
        """

        directories = set()
        for entry in package.namelist():
            if entry.endswith('/'):
                entry = entry[:-1]
                directories.add(entry)
            else:
                parent_dir = entry.split('/')[:-1]
                if len(parent_dir) > 0:
                    parent_dir = parent_dir[0]
                    directories.add(parent_dir)
        return directories



    def move_files(self, path_to_allep: str):
        """Move files to respective folders.

        Args:
            path_to_allep: Path to folder.
        """

        folders = {
            "library": "Library",
            "pythonpart_scripts": "PythonPartsScripts",
            "actionbar": "PythonPartsActionbar",
        }

        self.valid_folders.update(update_valid_folders(self.installation.target_location))

        with ZipFile(path_to_allep, "r") as package:
            directories = self.get_directories(package)
            for key, value in folders.items():
                if (val := getattr(self.installation, key, None)):

                    if val and val not in directories:
                        raise ValueError("Folder specified in the install config does not exist in the plugin")

            path = self.installation.get_path_function()
            for x, info in package.NameToInfo.items():
                if (x.count("/") < 2 and x[-1] == "/") or x.endswith(".yml"):
                    continue

                attr = x.split("/")[0]

                for key, _ in folders.items():
                    directory_name = None
                    if attr == getattr(self.installation, key, None) or attr in self.valid_folders:
                        directory_name = attr
                        break

                if not directory_name:
                    continue

                library      = f"{path}{directory_name}"


                directory_path = self._make_directory(library)
                info.filename  = "/".join(info.filename.split("/")[1:])


                self.tracked_files.append(self.split_by_target_location(os.path.join(directory_path, info.filename)))

                package.extract(member = info, path = directory_path)

            if self.installation.py_packages:
                lib_path = self._get_std_path()
                package.extract(self.installation.py_packages, path = lib_path)
                self.tracked_files.append(self.split_by_target_location(os.path.join(lib_path, self.installation.py_packages)))


    @classmethod
    def create(cls, path_to_allp: str) -> Self:
        """Helper function to create class Instance.

        Args:
            path_to_allp: Path to allep folder.
        Returns:
            CopyFiles: Instance of Copy File.
        """

        with ZipFile(path_to_allp) as package:
            with package.open("install-config.yml", "r") as file:
                config_data = yaml.safe_load(file)
                return cls.model_validate(config_data)

    def create_manifest_file(self) -> None:
        """ Create manifest file for Plugins"""

        path        = self.installation.get_path_function()
        folder_name = f"{path}AllepPlugins"
        file_path   = f"{folder_name}\\manifests.json"

        plugin_data = {
            "UUID"          : self.plugin.UUID,
            "pluginName"    : self.plugin.original_name,
            "developerName" : self.plugin.original_developer_name,
            "version"       : self.plugin.version,
            "filesCopied"   : self.tracked_files,
            "createdOn"     : str(date.today()),
            "ACTBFile"      : f"{self.split_by_target_location(self.get_file_location())}.actb" if self.tools and self.task_area  else "",
            "NPDFile"       : f"{self.split_by_target_location(self.get_file_location())}.npd"  if self.tools else "",
        }

        if not os.path.exists(file_path):
            try:
                os.makedirs(f"{folder_name}")
            except Exception as _:
                print("Allep Plugin Folder already exists.")

            with open(file_path, "w", encoding = "UTF-8") as file:
                json.dump({"plugins": [plugin_data]}, file)
        else:
            new_plugin = True

            with open(file_path, encoding = "UTF-8") as file:
                data = json.load(file)

                for index, plugin in enumerate(data["plugins"]):
                    if plugin.get("UUID","") == self.plugin.UUID:
                        data["plugins"][index] = plugin_data
                        new_plugin = False

            if new_plugin:
                data["plugins"].append(plugin_data)

            with open(file_path, "w", encoding="UTF-8") as file:
                json.dump(data, file)

        print("Manifest file creation complete.")

if __name__ == "__main__":
    pass
