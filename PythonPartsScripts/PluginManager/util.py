
"""Utility functions for uninstalling and installing Allep Packages"""
import contextlib
import datetime
import locale
import os
import shutil
import warnings

from collections.abc import Generator

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_Utility as AllplanUtil


# TODO: move the messages to the xml localization file
class Messages:
    """Enum of messages for install and update
    """

    FAIL_UPDATE      = "Failed to update. Unable to install the new version."
    FAIL_INSTALL     = "Failed to install."
    FAIL_UNISTALL    = "Failed to update. Unable to uninstall the existing version."

    SUCCESS_UPDATE   = "The following plugin has been successfully updated:"
    SUCCESS_INSTALL  = "The following plugin has been successfully installed:"
    SUCCESS_UNINSTALL = "The plugin has been successfully uninstalled:"

    @classmethod
    def get_success_message(cls, is_update: bool) -> str:
        """Get success message based on state.

        Args:
            is_update: Current state of installer.

        Returns:
            str: Message based on state.
        """

        return cls.SUCCESS_UPDATE if is_update else cls.SUCCESS_INSTALL

    @classmethod
    def get_fail_message(cls, is_update: bool)-> str:
        """Get fail message based on state.

        Args:
            is_update: Current state of installer.

        Returns:
            str: Message based on state.
        """

        return cls.FAIL_UPDATE if is_update else cls.FAIL_INSTALL

# TODO: opening and closing the progress bar should be done in the ScriptObject class
def close_progress_bar(progress_bar: AllplanUtil.ProgressBar | None):
    """Helper function for close progressbar.

    Args:
        progress_bar: Instance of progressbar.
    """

    if progress_bar is None:
        return

    progress_bar.CloseProgressbar()

def date_to_str(date: datetime.date) -> str:
    """Convert a date to a string in the user's default locale.

    Args:
        date: Date to convert.

    Returns:
        str: Date as a string in the user's default locale.
    """
    current_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, '')
    date_as_str = date.strftime('%x')
    locale.setlocale(locale.LC_TIME, current_locale)
    return date_as_str

def delete_folder(path: str):
    """Delete folder with supressing OSError.

    Args:
        path : Path of the folder.
    """

    with contextlib.suppress(OSError):
        os.rmdir(path)
        print(f"Deleting folder {path}")

# TODO: use FileNameService.get_global_standard_path instead of get_path_function
def get_path_function(target: str) -> str:
    """ Get path function based of target folder.
    Args:
        target: The target location of plugin, Should be one of (Etc, Std, Usr)

    Returns:
        str: Full path of folder.
    """

    if target == "Etc":
        return AllplanSettings.AllplanPaths.GetEtcPath()

    if target == "Std":
        return AllplanSettings.AllplanPaths.GetStdPath()

    return AllplanSettings.AllplanPaths.GetUsrPath()

def get_full_path(target_folder: str) -> str:
    """ Get full path of manifest file.

    Args:
        target_folder : Target directory in (USR, STD, ETC).

    Returns:
        str: Full path to manifest file.
    """

    path = get_path_function(target_folder)

    return f"{path}AllepPlugins\\manifests.json"


def make_step_progress_bar(step: int, title: str, progress_bar: AllplanUtil.ProgressBar | None):
    """Helper function for progressbar.
    Args:
        step            : The amount of steps to move the progress bar forward.
        title           : Tile of Progress bar.
        progress_bar    : Instance of progressbar.
    """

    if progress_bar is None:
        return

    progress_bar.SetTitle(title)
    progress_bar.MakeStep(step)

@contextlib.contextmanager
def notify_user(success_msg: str|None, error_msg: str) -> Generator:
    """Context manager to catch warnings and errors and show them to the user
    in a message box.

    In case of errors, the error message is shown to the user. The exception is also raised
    to provide more information in the trace.

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
            raise

        if success_msg is None:
            return
        msg = success_msg

        if wrng:
            msg += " Following warnings appeared:"
        for i, warning in enumerate(wrng):
            msg += f"\n{i}. {warning.message}"

        AllplanUtil.ShowMessageBox(msg, AllplanUtil.MB_OK)

def remove_directory(path: str):
    """Remove directories recursively and suppress OsError in case of nonempty directories

    Args:
        path: Path of the directory

    """

    if not os.path.exists(path) or not os.path.isdir(path):
        print(f"Path {path} does not exist.")
        return

    for entry in os.scandir(path):
        if entry.is_dir():
            remove_directory(entry.path)
            delete_folder(entry.path)

            if "__pycache__" in entry.name:
                shutil.rmtree(entry.path)

        elif "_pyp"in entry.name:
            os.remove(entry.path)


    if os.path.exists(path):
        delete_folder(path)
