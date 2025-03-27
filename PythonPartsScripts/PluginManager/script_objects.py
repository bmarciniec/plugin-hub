"""Module with the script object handling the workflow of the plugin hub"""
import re
import sys
import webbrowser

from pathlib import Path
from uuid import UUID

import NemAll_Python_Utility as AllplanUtil

from BaseScriptObject import BaseScriptObject, BaseScriptObjectData
from BuildingElement import BuildingElement
from CreateElementResult import CreateElementResult
from packaging.version import Version
from requests.exceptions import ConnectionError
from ScriptObjectInteractors.OnCancelFunctionResult import OnCancelFunctionResult

from .allep import AllepPackage
from .installer import AllepInstaller
from .plugins import Plugin, PluginsCollection, PluginStatus
from .util import notify_user


class PluginManagerScript(BaseScriptObject):
    """Class for analyzing a polygon"""

    def __init__(self,
                 build_ele         : BuildingElement,
                 script_object_data: BaseScriptObjectData):
        """Initialization of the script for the plugin hub

        Args:
            build_ele:          building element with the parameter properties
            script_object_data: script object data
        """
        super().__init__(script_object_data)

        # Installation per drag and drop
        if sys.argv and sys.argv != [""]:
            allep_path   = Path(sys.argv)    #type: ignore
            package      = AllepPackage(allep_path.name, local_path=allep_path)
            progress_bar = AllplanUtil.ProgressBar(100, 0, False)

            with notify_user(success_msg  = f"{allep_path.name} installed successfully.",
                             error_msg    = "Installation failed.",
                             progress_bar = progress_bar):

                installer = AllepInstaller(package)
                installer.install_from_local_file()

            sys.argv = [""]
            self.coord_input.CancelInput()

            # return

        self.build_ele = build_ele

        # Get the plugins from the GitHub repository sorted by name
        self.plugins = PluginsCollection()

        try:
            self.plugins.get_plugins_from_github()
        except ConnectionError:
            pass

        self.plugins.get_installed_plugins()
        self.plugins.update_plugins_overview_on_palette(self.build_ele)

    def execute(self) -> CreateElementResult:
        """Execute the element creation

        Returns:
            nothing, because there is no element to create
        """
        return CreateElementResult()

    def on_control_event(self, event_id: int) -> bool:
        """Handle the event of pressing a button control

        Args:
            event_id: ID of the button control

        Returns:
            True, if after the event, the palette needs to be updated
        """
        plugin_index = event_id >> 16
        action_id  = event_id - (plugin_index << 16)

        if 1500 < action_id < 2000:   # when button was clicked on the detail page
            plugin = self.plugins[UUID(self.build_ele.PluginUUID.value)]

        else: # when button was clicked on the overview page
            installed_plugins = [plugin for plugin in self.plugins if plugin.status != PluginStatus.NOT_INSTALLED]
            available_plugins = [plugin for plugin in self.plugins if plugin.status == PluginStatus.NOT_INSTALLED]

            if 1200 < action_id < 1500:
                plugin = available_plugins[plugin_index]
            else:
                plugin = installed_plugins[plugin_index]

        if action_id in (self.build_ele.SHOW_DETAILS_AVAILABLE_PLUGIN, self.build_ele.SHOW_DETAILS_INSTALLED_PLUGIN):
            plugin.update_plugin_details_on_palette(self.build_ele)
            self.build_ele.CurrentPaletteState.value = self.build_ele.SHOW_DETAILS
            return True

        match action_id:
            case self.build_ele.INSTALL | self.build_ele.INSTALL_AVAILABLE_PLUGIN:
                msg = f"You are about to install {plugin.name}.\nWould you like to proceed?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                developer_name = plugin.developer.name or plugin.developer.id
                progress_bar   = AllplanUtil.ProgressBar(200, 0, False)  # 100 steps for download and 100 for installation

                with notify_user(success_msg  = f"{plugin.name} installed successfully.\n\nDeveloper: {developer_name}",
                                 error_msg    = "Installation failed.",
                                 progress_bar = progress_bar):
                    plugin.install(progress_bar)

                plugin.update_plugin_details_on_palette(self.build_ele, only_status=True)
                self.plugins.update_plugins_overview_on_palette(self.build_ele)
                return True

            case self.build_ele.CHECK_ALL_FOR_UPDATES:

                # check for updates; show progress bar

                progress_bar = AllplanUtil.ProgressBar(len(self.plugins) * 10 + 10, 0, False)
                plugins_to_update = list[Plugin]()

                with notify_user(None, "Not able to check the updates.", progress_bar):
                    for plugin in self.plugins:
                        plugin.check_releases(progress_bar)

                        if plugin.status == PluginStatus.UPDATE_AVAILABLE:
                            plugins_to_update.append(plugin)

                # all plugins are up to date

                if not plugins_to_update:
                    AllplanUtil.ShowMessageBox("All plugins are up to date.", AllplanUtil.MB_OK)
                    return False

                # prepare message with plugins that have updates available

                msg = "The following plugins have updates available:\n"

                for plugin in plugins_to_update:
                    msg += f"\n{plugin.name} ({plugin.installed_version} -> {plugin.latest_compatible_release.version})"

                msg += "\n\nDo you want to proceed with the updates?"

                with notify_user(None, "Not able to update the plugins."):
                    if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                        return False

                progress_bar = AllplanUtil.ProgressBar(len(plugins_to_update) * 260 + 10, 0, False)

                with notify_user(success_msg  = "Plugins updated successfully.",
                                 error_msg    = "Update failed.",
                                 progress_bar = progress_bar):
                    for plugin in plugins_to_update:
                        progress_bar.SetTitle(f"Updating {plugin.name}...")
                        plugin.uninstall(progress_bar)
                        plugin.install(progress_bar)
                        plugin.update_plugin_details_on_palette(self.build_ele, only_status=True)

                return True

            case self.build_ele.CHECK_FOR_UPDATES:

                with notify_user(None, f"Not able to check the updates for {plugin.name}."):
                    plugin.check_releases()

                if plugin.status == PluginStatus.UP_TO_DATE:
                    msg = f"The currently installed version of {plugin.name} ({plugin.installed_version}) is up to date."
                    AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_OK)
                    return False

                if plugin.status == PluginStatus.UPDATE_AVAILABLE:
                    msg = f"New version {plugin.latest_compatible_release.version} is available. Do you want to proceed with the update?"

                    if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                        return False

                    progress_bar = AllplanUtil.ProgressBar(270, 0, False) # 70 for uninstallation, 100 steps for download, 90 for installation, 10 margin

                    with notify_user(success_msg  = "Plugin updated successfully.",
                                     error_msg    = "Update failed.",
                                     progress_bar = progress_bar):

                        plugin.uninstall(progress_bar)
                        plugin.install(progress_bar)
                        plugin.update_plugin_details_on_palette(self.build_ele, only_status=True)

                    return True

                return False

            case self.build_ele.INSTALL_ANOTHER_VERSION:
                combo_box = self.build_ele.get_existing_property("VersionsComboBox")
                self.control_props_util.set_visible_condition("InstallAnotherVersionRow", "True")

                with notify_user(None, f"Not able to get the releases of {plugin.name}."):
                    plugin.check_releases()

                plugin.fill_versions_combo_box(combo_box, self.control_props_util)
                return True

            case self.build_ele.EXECUTE_INSTALL_ANOTHER_VERSION:
                # From a string like "1.0.0 (3 wks ago, latest)" get only the version number
                version_str = re.match(r"^[^(]+", self.build_ele.VersionsComboBox.value).group().strip()
                version = Version(version_str)

                if isinstance(plugin.installed_version, Version) and version < plugin.installed_version:
                    msg = f"You are about to downgrade {plugin.name} to version {version}.\n\n"
                    msg += "IMPORTANT: Downgrading a plugin may cause the PythonParts that are placed in the model"
                    msg += " with the newer version to become unmodifiable.\n\nWould you like to proceed?"

                else:
                    msg = f"You are about to install {plugin.name} version {version}.\nWould you like to proceed?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                progress_bar = AllplanUtil.ProgressBar(270, 0, False) # 70 for uninstallation, 100 steps for download, 90 for installation, 10 margin

                with notify_user(success_msg  = f"{plugin.name} version {version} installed successfully.",
                                 error_msg    = "Installation failed.",
                                 progress_bar = progress_bar):
                    plugin.uninstall(progress_bar)
                    plugin.install(progress_bar, version)

                plugin.update_plugin_details_on_palette(self.build_ele, only_status=True)

                return True

            case self.build_ele.UPDATE:
                msg = f"You are about to update {plugin.name} from {plugin.installed_version} to {plugin.latest_compatible_release}.\nWould you like to proceed?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                progress_bar = AllplanUtil.ProgressBar(270, 0, False) # 70 for uninstallation, 100 steps for download, 90 for installation, 10 margin

                with notify_user(success_msg   = "Plugin updated successfully.",
                                 error_msg     = "Update failed.",
                                 progress_bar  = progress_bar):
                    plugin.uninstall(progress_bar)
                    plugin.install(progress_bar)

                plugin.update_plugin_details_on_palette(self.build_ele, only_status=True)

                return True

            case self.build_ele.UNINSTALL:
                msg = f"Are you sure you want to uninstall {plugin.name}?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                progress_bar = AllplanUtil.ProgressBar(80, 0, False)
                with notify_user(success_msg   = "Plugin uninstalled successfully.",
                                 error_msg     = "Uninstallation failed.",
                                 progress_bar  = progress_bar):
                    plugin.uninstall(progress_bar)

                self.plugins.clean_up()
                self.plugins.update_plugins_overview_on_palette(self.build_ele)
                self.build_ele.CurrentPaletteState.value = self.build_ele.SHOW_OVERVIEW

                return True

            case self.build_ele.GO_TO_GITHUB:
                if plugin.has_github:
                    webbrowser.open(f"https://github.com/{plugin.github['owner']}/{plugin.github['repo']}/")
                return False

            case self.build_ele.GO_TO_HOMEPAGE:
                webbrowser.open(plugin.developer.homepage)
                return False

            case self.build_ele.EMAIL_TO_SUPPORT:
                webbrowser.open(f"mailto:{plugin.developer.support.email}")
                return False

        return False

    def on_cancel_function(self) -> OnCancelFunctionResult:
        """Handle the event of hitting the close button or escape key

        Returns:
            OnCancelFunctionResult: what should happen after the cancel event
        """
        if self.build_ele.CurrentPaletteState.value == self.build_ele.SHOW_DETAILS:
            self.control_props_util.set_visible_condition("InstallAnotherVersionRow", "False")

            self.build_ele.CurrentPaletteState.value = self.build_ele.SHOW_OVERVIEW
            if self.exec_palette_update is not None:
                self.exec_palette_update()
            return OnCancelFunctionResult.CONTINUE_INPUT

        return OnCancelFunctionResult.CANCEL_INPUT
