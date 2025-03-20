"""Module to run the tests for the Plugin manager."""
import os
import sys
import unittest
import winreg

from pathlib import Path

ALLPLAN_VERSION = 99.0
CODELINE = "MAIN_VisualEditor"

def add_python_paths():
    sys.path.append(os.getcwd())

    # Read the registry values

    key_path = f"SOFTWARE\\NEMETSCHEK\\{CODELINE}\\{str(ALLPLAN_VERSION)}\\InstallRoot"
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)

    program_data_drive, _ = winreg.QueryValueEx(key, "ProgramDataDrive")
    program_data_path, _ = winreg.QueryValueEx(key, "ProgramDataPath")
    program_drive, _ = winreg.QueryValueEx(key, "ProgramDrive")
    program_path, _ = winreg.QueryValueEx(key, "ProgramPath")

    winreg.CloseKey(key)

    etc_path = Path(program_data_drive + program_data_path + "/etc")
    prg_path = Path(program_drive + program_path)

    sys.path.append(str(etc_path / Path("PythonPartsFramework")))
    sys.path.append(str(etc_path / Path("PythonPartsFramework\\GeneralScripts")))
    sys.path.append(str(etc_path / Path("PythonPartsScripts")))
    sys.path.append(str(prg_path))

if __name__ == '__main__':
    add_python_paths()

    from tests import test_plugins, test_releases

    unittest.main(test_releases)
    unittest.main(test_plugins)
