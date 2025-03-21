"""Module with the script object handling the workflow of the plugin hub"""
import sys
import webbrowser

from pathlib import Path
from uuid import UUID

import NemAll_Python_Utility as AllplanUtil

from BaseScriptObject import BaseScriptObject, BaseScriptObjectData
from BuildingElement import BuildingElement
from CreateElementResult import CreateElementResult
from requests.exceptions import ConnectionError
from ScriptObjectInteractors.OnCancelFunctionResult import OnCancelFunctionResult

from .allep import AllepPackage
from .installer import AllepInstaller
from .plugins import PluginsCollection, PluginStatus
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
        self.plugins.update_building_element(self.build_ele)

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
        else:                   # when button was clicked on the overview page
            plugin = self.plugins[plugin_index]

        match action_id:
            case self.build_ele.INSTALL:
                developer_name = plugin.developer.name or plugin.developer.id
                progress_bar   = AllplanUtil.ProgressBar(200, 0, False)  # 100 steps for download and 100 for installation

                with notify_user(success_msg  = f"{plugin.name} installed successfully.\n\nDeveloper: {developer_name}",
                                 error_msg    = "Installation failed.",
                                 progress_bar = progress_bar):
                    plugin.install(progress_bar)

                self.plugins.update_building_element(self.build_ele, only_status=True)
                return True

            case self.build_ele.SHOW_DETAILS:
                plugin.show_details_on_palette(self.build_ele)
                self.build_ele.CurrentPaletteState.value = self.build_ele.SHOW_DETAILS
                return True

            case self.build_ele.GO_TO_HOMEPAGE:
                webbrowser.open(plugin.developer.homepage)

            case self.build_ele.CHECK_FOR_UPDATES:

                with notify_user(None, f"Not able to check the updates for {plugin.name}."):
                    plugin.check_latest_release()

                if plugin.status == PluginStatus.UP_TO_DATE:
                    msg = f"The currently installed version of {plugin.name} ({plugin.installed_version}) is up to date."
                    AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_OK)

                elif plugin.status == PluginStatus.UPDATE_AVAILABLE:
                    msg = f"New version {plugin.latest_compatible_release} is available. Do you want to proceed with the update?"

                    if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDYES:
                        progress_bar = AllplanUtil.ProgressBar(180, 0, False)

                        with notify_user(success_msg  = "Plugin updated successfully.",
                                         error_msg    = "Update failed.",
                                         progress_bar = progress_bar):
                            plugin.uninstall(progress_bar)
                            plugin.install(progress_bar)

                self.plugins.update_building_element(self.build_ele, only_status=True)
                return True

            case self.build_ele.EMAIL_TO_SUPPORT:
                webbrowser.open(f"mailto:{plugin.developer.support.email}")
                return False

            case self.build_ele.UPDATE:
                msg = f"You are about to update {plugin.name} from {plugin.installed_version} to {plugin.latest_compatible_release}.\nWould you like to Proceed?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                progress_bar = AllplanUtil.ProgressBar(270, 0, False) # 70 for uninstallation, 100 steps for download, 90 for installation, 10 margin

                with notify_user(success_msg   = "Plugin updated successfully.",
                                 error_msg     = "Update failed.",
                                 progress_bar  = progress_bar):
                    plugin.uninstall(progress_bar)
                    plugin.install(progress_bar)

                self.plugins.update_building_element(self.build_ele, only_status=True)
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
                self.plugins.update_building_element(self.build_ele, only_status=False)
                return True

        return False

    def on_cancel_function(self) -> OnCancelFunctionResult:
        """Handle the event of hitting the close button or escape key

        Returns:
            OnCancelFunctionResult: what should happen after the cancel event
        """
        if self.build_ele.CurrentPaletteState.value == self.build_ele.SHOW_DETAILS:
            self.build_ele.CurrentPaletteState.value = self.build_ele.SHOW_OVERVIEW
            return OnCancelFunctionResult.CONTINUE_INPUT

        return OnCancelFunctionResult.CANCEL_INPUT
