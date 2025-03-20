"""Module containing allep package installer."""
import glob

from pathlib import Path
from typing import Self
from xml.etree import ElementTree as ET

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_Utility as AllplanUtil

from pydantic import ValidationError

from . import exceptions
from .allep import AllepPackage
from .copy_files import CopyFiles
from .site_libraries.packaging.version import Version
from .util import Messages, make_step_progress_bar

ALLPLAN_VERSION = Version(AllplanSettings.AllplanVersion.Version())

class AllepInstaller:
    """Class to install the plugin."""

    def __init__(self, package: AllepPackage, update: bool = False):
        """Initialization of the Plugin Installer.

        Args:
            package: Allep package to be installed
            update: False, when plugin is being newly installed. True when it's being updated.
        """
        self.file_copier : CopyFiles|None = None

        self.allep_package = package
        self.is_update     = update

    def download_and_install_package(self, progress_bar: AllplanUtil.ProgressBar|None = None):
        """Download and install the package.

        Args:
            progress_bar: Instance of progress bar. When provided, it will be increased by 190 steps
        """
        if not self.allep_package.downloaded:
            tmp_path = Path(AllplanSettings.AllplanPaths.GetTmpPath())
            self.allep_package.download(tmp_path, progress_bar)

        self.install_from_local_file(progress_bar)
        self.allep_package.delete_local_file()

    def install_from_local_file(self, progress_bar: AllplanUtil.ProgressBar|None = None):
        """ execute the package installation

        Args:
            progress_bar: Instance of progress bar. When provided, it will be increased by 90 steps

        Raises:
            PackageExtractionError   : raised if there is an error during extraction.
            InstallRequirementsError : raised if there is an error installing requirements.
            CreateActionBarError     : raised if there is an error during creation of actb or npd file.
        """
        make_step_progress_bar(20, "Copying contents", progress_bar)
        self.file_copier = CopyFiles.create(self.allep_package.local_path)    # type: ignore

        make_step_progress_bar(20, "Extracting package", progress_bar)
        self._extract_allep()

        make_step_progress_bar(20, "Downloading dependencies", progress_bar)
        self._install_requirements()

        make_step_progress_bar(20, "Creating NPD & ACTB files", progress_bar)
        self.file_copier.write_file()

        make_step_progress_bar(10, "Updating manifest file", progress_bar)
        self._update_pyp_file()

        self.file_copier.create_manifest_file()


    def _extract_allep(self):
        """Extract package to relevant folders.

        Raises:
            PackageExtractionError: Error in reading Install Config or no ALLEP package attached to the plugin.
            MinimumAllplanVersionError: Minimum version speacified is greater than current ALLPLAN version.
            AbortInstallError: An exception is rasied to Abort Installation.
        """

        try:
            if self.file_copier.plugin.min_version > ALLPLAN_VERSION.major:
                raise exceptions.MinimumAllplanVersionError(f"Unable to install the plugin. It requires ALLPLAN {self.file_copier.plugin.min_version} or newer")

            self.file_copier.move_files(self.allep_package.local_path)

        except exceptions.AbortInstallError as e:
            raise exceptions.AbortInstallError from e
        except ValidationError as e:
            raise exceptions.PackageExtractionError(self._parse_pydantic_error(e)) from e
        except Exception as e:
            raise exceptions.PackageExtractionError(self._parse_native_error(e)) from e

    def _install_requirements(self) -> Self:
        """Install requirements files.

        Returns:
            installer: Instance of copy files.
        Raises:
            InstallRequirementsError: Error in case of installation of packages.
        """

        try:
            req_file = f"{self.file_copier._get_std_path()}\\{self.file_copier.installation.py_packages}"
            self.file_copier.installation.install_pypackages(req_file)
            return self

        except Exception as e:
            raise exceptions.InstallRequirementsError(self._parse_native_error(e))

    def _parse_native_error(self, e: Exception) -> str:
        """Parse native python error messages

        Args:
            e  : Instance of Native Python error.

        Returns:
            str: Error Message.
        """
        return f"{Messages.get_fail_message(self.is_update)}\n" + f"{type(e).__name__} : {str(e).replace("archive", "plugin")}"

    def _update_pyp_file(self):
        """Update pyp file to include valid path of pyp.

        Raises:
            Exception: In case pyp file update fails.
        """
        lib_folder = self.file_copier._get_lib_path()

        try:
            pyp_files  = glob.glob(f"{lib_folder}\\**\\*.pyp", recursive= True)
            for file in pyp_files:
                pyp_file_xml = ET.parse(file)
                root         = pyp_file_xml.getroot()
                name         = root.findall("Script")[0].findall("Name")[0]
                name.text    = f"AllepPlugins\\{self.file_copier.plugin.developer}\\{self.file_copier.plugin.name}\\{name.text}"

                pyp_file_xml.write(file)
            return

        except Exception as e:
            raise Exception(self._parse_native_error(e)) from e

    def _parse_pydantic_error(self, e: ValidationError) -> str:
        """Parse validation error raised from Pydantic.

        Args:
            e  : Instance of Validation Error.

        Returns:
            str: Error Message.
        """

        message = f"{Messages.get_fail_message(self.is_update)}\n{e.error_count()} Validation Errors\n"
        for x in e.errors():
            if "string" in x["type"]:
                msg = "The value is invalid or empty and could not be converted to a string.\n"
            else:
                msg = f"{x["msg"]}\n"
            message = message + f"{x["loc"][-1]}: {msg}"
        return message
