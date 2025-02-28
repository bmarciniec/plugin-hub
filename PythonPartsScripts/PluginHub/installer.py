"""Module containing allep package installer."""
import glob

from pathlib import Path
from typing import Self
from xml.etree import ElementTree as ET

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_Utility as AllplanUtil

from pydantic import ValidationError
from PythonPartActionBarUtil.YamlUtil import installer_exception
from PythonPartActionBarUtil.YamlUtil.copy_files import CopyFiles
from PythonPartActionBarUtil.YamlUtil.util import Messages, close_progress_bar, make_step_progress_bar

from .allep import AllepPackage
from .site_libraries.version import Version

ALLPLAN_VERSION = Version(AllplanSettings.AllplanVersion.Version())

class AllepInstaller:
    """Class to install the plugin."""

    def __init__(self, package: AllepPackage, update: bool = False):
        """Initialization of the Plugin Installer.

        Args:
            package: Allep package to be installed
            update: False, when plugin is being newly installed. True when it's being updated.
        """
        self.installer : CopyFiles|None = None

        self.allep_package    = package
        self.is_update        = update

    def download_and_install_package(self, progress_bar: AllplanUtil.ProgressBar|None = None):
        """Download and install the package.

        Args:
            progress_bar: Instance of progress bar.
        """
        if not self.allep_package.downloaded:
            make_step_progress_bar(0, "Downloading the plugin", progress_bar)
            self.allep_package.download(Path(AllplanSettings.AllplanPaths.GetTmpPath()))

        self.install_from_local_file(progress_bar)
        self.allep_package.delete_local_file()

    def install_from_local_file(self, progress_bar: AllplanUtil.ProgressBar|None = None):
        """ execute the package installation

        Args:
            progress_bar: Instance of progress bar.

        Raises:
            PackageExtractionError   : raised if there is an error during extraction.
            InstallRequirementsError : raised if there is an error installing requirements.
            CreateActionBarError     : raised if there is an error during creation of actb or npd file.
        """

        try:
            make_step_progress_bar(20, "Copying contents", progress_bar)
            self.installer = CopyFiles.create(self.allep_package.local_path)    # type: ignore

            make_step_progress_bar(20, "Extracting package", progress_bar)
            self._extract_allep()

        except installer_exception.AbortInstallError as _:
            close_progress_bar(progress_bar)
            return

        except installer_exception.PackageExtractionError as e:
            close_progress_bar(progress_bar)
            raise installer_exception.PackageExtractionError from e

        try:
            make_step_progress_bar(20, "Downloading dependencies", progress_bar)
            self._install_requirements()

        except installer_exception.InstallRequirementsError as e:
            close_progress_bar(progress_bar)
            raise installer_exception.InstallRequirementsError from e

        try:
            make_step_progress_bar(20, "Creating NPD & ACTB files", progress_bar)
            self.installer.write_file()

        except installer_exception.CreateActionBarError as e:
            close_progress_bar(progress_bar)
            raise installer_exception.CreateActionBarError from e

        make_step_progress_bar(5, "Updating manifest file", progress_bar)
        self._update_pyp_file()

        self.installer.create_manifest_file()

        make_step_progress_bar(5, "Completed", progress_bar)
        close_progress_bar(progress_bar)


    def _extract_allep(self):
        """Extract package to relevant folders.

        Raises:
            PackageExtractionError: Error in reading Install Config or no ALLEP package attached to the plugin.
            MinimumAllplanVersionError: Minimum version speacified is greater than current ALLPLAN version.
            AbortInstallationError: An exception is rasied to Abort Installation.
        """

        try:
            if self.installer.plugin.min_version > ALLPLAN_VERSION.major:
                raise installer_exception.MinimumAllplanVersionError(f"Unable to install the plugin. It requires ALLPLAN {self.installer.plugin.min_version} or newer")

            # TODO: Move this logic to PluginCollection
            # if (plugin := self.is_plugin_installed()) is not None:
            #     self.is_update = True

            #     if not check_plugin_version_eqaul(plugin["version"], self.installer.plugin.version):
            #         close_progress_bar(self.progress_bar)
            #         proceed = AllplanUtil.ShowMessageBox(f"Do you want to override the following installed plugin?"\
            #                                              f"\n{self.installer.plugin.name}\n{self.installer.plugin.developer}\n"\
            #                                              f"{plugin["version"]} -> {self.installer.plugin.version}", AllplanUtil.MB_YESNO)

            #         if proceed == AllplanUtil.IDNO:
            #             raise installer_exception.AbortInstallError()

            #         self.progress_bar = AllplanUtil.ProgressBar(100, 0, False)

            #         # We do a 40 step jump here to make sure we get back to 60% since restarting progress bar.
            #         make_step_progress_bar(40, "Removing Directory", self.progress_bar)
            #         uninstall_plugins(plugin)
            #     else:
            #         raise Exception("The latest version of the plugin is already installed.")

            self.installer.move_files(self.allep_package.local_path)

        except installer_exception.AbortInstallError as e:
            raise installer_exception.AbortInstallError from e
        except ValidationError as e:
            raise installer_exception.PackageExtractionError(self._parse_pydantic_error(e)) from e
        except Exception as e:
            raise installer_exception.PackageExtractionError(self._parse_native_error(e)) from e

    def _install_requirements(self) -> Self:
        """Install requirements files.

        Returns:
            installer: Instance of copy files.
        Raises:
            InstallRequirementsError: Error in case of installation of packages.
        """

        try:
            req_file = f"{self.installer._get_std_path()}\\{self.installer.installation.py_packages}"
            self.installer.installation.install_pypackages(req_file)
            return self

        except Exception as e:
            raise installer_exception.InstallRequirementsError(self._parse_native_error(e))

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
        lib_folder = self.installer._get_lib_path()

        try:
            pyp_files  = glob.glob(f"{lib_folder}\\**\\*.pyp", recursive= True)
            for file in pyp_files:
                pyp_file_xml = ET.parse(file)
                root         = pyp_file_xml.getroot()
                name         = root.findall("Script")[0].findall("Name")[0]
                name.text    = f"AllepPlugins\\{self.installer.plugin.developer}\\{self.installer.plugin.name}\\{name.text}"

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

