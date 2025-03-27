"""Module to run the tests for the Plugin manager."""
import importlib
import os
import sys
import unittest
import winreg

from pathlib import Path
from pdb import run
from unittest.mock import patch


def add_python_paths(code_line: str, allplan_version: float):
    # Read the registry values

    key_path = f"SOFTWARE\\NEMETSCHEK\\{code_line}\\{str(allplan_version)}\\InstallRoot"
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)

    program_data_drive, _ = winreg.QueryValueEx(key, "ProgramDataDrive")
    program_data_path, _ = winreg.QueryValueEx(key, "ProgramDataPath")
    program_drive, _ = winreg.QueryValueEx(key, "ProgramDrive")
    program_path, _ = winreg.QueryValueEx(key, "ProgramPath")

    winreg.CloseKey(key)

    etc_path = Path(program_data_drive + program_data_path + "/etc")
    prg_path = Path(program_drive + program_path)

    sys.path.append(os.getcwd())
    sys.path.append(os.getcwd() + "/PythonPartsScripts")
    sys.path.append(str(etc_path / Path("PythonPartsFramework")))
    sys.path.append(str(etc_path / Path("PythonPartsFramework\\GeneralScripts")))
    sys.path.append(str(etc_path / Path("PythonPartsScripts")))
    sys.path.append(str(etc_path / Path("PythonParts-site-packages")))
    sys.path.append(str(prg_path))

def run_tests():
    from tests.mocks import PathConstantsMock
    with patch('PathConstants.PathConstants', new = PathConstantsMock()):

        suite = unittest.TestSuite()

        for test_name in ("plugins_collection", "releases", "plugin"):
            test_module = importlib.import_module(f'tests.test_{test_name}')
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_module))

        runner = unittest.TextTestRunner()
        runner.run(suite)


if __name__ == '__main__':
    add_python_paths("MAIN_VisualEditor", 99.0)
    run_tests()
