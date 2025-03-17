"""Module with the script object handling the workflow of the plugin hub"""
import warnings
import webbrowser

from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

import NemAll_Python_Utility as AllplanUtil

from BaseScriptObject import BaseScriptObject, BaseScriptObjectData
from BuildingElement import BuildingElement
from CreateElementResult import CreateElementResult
from ScriptObjectInteractors.OnCancelFunctionResult import OnCancelFunctionResult

from .plugins import PluginsCollection, PluginStatus


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
        self.build_ele = build_ele

        # Get the plugins from the GitHub repository sorted by name
        self.plugins = PluginsCollection()
        self.plugins.get_plugins_from_github()
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

        if plugin_index == 0:   # when button was clicked on the detail page
            plugin = self.plugins[UUID(self.build_ele.PluginUUID.value)]
        else:                   # when button was clicked on the overview page
            plugin = self.plugins[plugin_index]

        match action_id:
            case self.build_ele.INSTALL:
                success_msg = f"{plugin.name} installed successfully.\n\nDeveloper: {plugin.developer}"

                with notify_user(success_msg, "Installation failed."):
                    plugin.install(AllplanUtil.ProgressBar(100, 0, False))
                    self.plugins.update_building_element(self.build_ele, only_status=True)

                return True

            case self.build_ele.SHOW_DETAILS:
                plugin.fill_palette(self.build_ele)
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
                    msg = f"New version {plugin.latest_version} is available. Do you want to proceed with the update?"

                    if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDYES:
                        with notify_user("Plugin updated successfully.", "Update failed."):
                            # TODO: use one progress bar
                            plugin.uninstall(AllplanUtil.ProgressBar(100, 0, False))
                            plugin.install(AllplanUtil.ProgressBar(100, 0, False))

                self.plugins.update_building_element(self.build_ele, only_status=True)
                return True

            case self.build_ele.EMAIL_TO_SUPPORT:
                webbrowser.open(f"mailto:{plugin.developer.support.email}")
                return False

            case self.build_ele.UPDATE:
                msg = f"You are about to update {plugin.name} from {plugin.installed_version} to {plugin.latest_version}.\nWould you like to Proceed?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                with notify_user("Plugin updated successfully.", "Update failed."):
                    # TODO: use one progress bar
                    plugin.uninstall(AllplanUtil.ProgressBar(100, 0, False))
                    plugin.install(AllplanUtil.ProgressBar(100, 0, False))

                self.plugins.update_building_element(self.build_ele, only_status=True)
                return True

            case self.build_ele.UNINSTALL:
                msg = f"Are you sure you want to uninstall {plugin.name}?"

                if AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_YESNO) == AllplanUtil.IDNO:
                    return False

                with notify_user("Plugin uninstalled successfully.", "Uninstallation failed."):
                    plugin.uninstall(AllplanUtil.ProgressBar(100, 0, False))

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

@contextmanager
def notify_user(success_msg: str|None, error_msg: str) -> Generator:
    """Context manager to catch warnings and errors and show them to the user
    in a message box.

    In case of errors, the error message is shown to the user.

    In case of success, the success message (if specified) is shown to the user.
    Warnings (if any) are appended to the message.

    Args:
        success_msg: message to show in case of success; None if no message should be shown
        error_msg: message to show in case of error

    Yields:
        list of warnings that appeared during the execution
    """
    with warnings.catch_warnings(record=True) as wrng:
        warnings.simplefilter("always")  # Ensure all warnings are caught
        try:
            yield wrng
        except Exception as err:    # pylint: disable=broad-except
            AllplanUtil.ShowMessageBox(f"{error_msg}\n{err}", AllplanUtil.MB_OK)
        else:
            if success_msg is None:
                return
            msg = success_msg

            if wrng:
                msg += " Following warnings appeared:"
            for i, warning in enumerate(wrng):
                msg += f"\n{i}. {warning.message}"

            AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_OK)
