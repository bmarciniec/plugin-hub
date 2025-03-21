import unittest

from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch
from uuid import UUID

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from PluginManager.allep import AllepPackage
from PluginManager.developers import Developer
from PluginManager.plugins import InstallLocations, Plugin, PluginStatus

from tests.mocks import mocked_requests_get


class TestPlugin(unittest.TestCase):

    def setUp(self):
        self.plugin_github_data = {
            "uuid": "52686573-ac50-47da-9426-96e0db791b96",
            "name": "Test Plugin",
            "developer": "example-developer",
            "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "github": {
                "owner": "owner",
                "repo": "repo"
            },
            "compatibility": "~=1.0"
        }


        self.plugin_from_github = Plugin.from_github_data(self.plugin_github_data)

        self.installed_plugin_data = {
            "UUID": "52686573-ac50-47da-9426-96e0db791b96",
            "pluginName": "Test Plugin",
            "developerName": "Example developer",
            "version": "1.0.0",
            "filesCopied": [
            "Usr\\Local\\Library\\example-developer\\ExampleImage1.png",
            "Usr\\Local\\Library\\example-developer\\ExampleScript1.pyp",
            "Usr\\Local\\PythonPartsActionbar\\example-developer\\ExampleIcon1_128.png",
            "Usr\\Local\\PythonPartsActionbar\\example-developer\\ExampleIcon1_24.png",
            "Usr\\Local\\PythonPartsScripts\\example-developer\\ExampleScript1.py",
            ],
            "createdOn": "2025-03-17",
            "ACTBFile": "Usr\\Local\\a3bb189e-8bf9-3888-9912-ace4e6543002.actb",
            "NPDFile": "Usr\\Local\\a3bb189e-8bf9-3888-9912-ace4e6543002.npd"
        }

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True):
            self.installed_plugin = Plugin.from_manifest_data(InstallLocations.USR, self.installed_plugin_data)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_plugin_from_github(self, _):
        """Test the initialization of a Plugin object."""
        self.assertEqual(self.plugin_from_github.uuid, UUID(self.plugin_github_data["uuid"]))
        self.assertEqual(self.plugin_from_github.name, self.plugin_github_data["name"])
        self.assertEqual(self.plugin_from_github.developer, self.plugin_github_data["developer"])
        self.assertEqual(self.plugin_from_github.description, self.plugin_github_data["description"])

        self.assertTrue(self.plugin_from_github.has_github)
        self.assertIsInstance(self.plugin_from_github.compatibility, SpecifierSet)

        self.plugin_from_github.check_releases()

        self.assertIsNotNone(self.plugin_from_github.latest_compatible_release)
        self.assertEqual(self.plugin_from_github.latest_compatible_release.version, Version("1.1.0"))
        self.assertFalse(self.plugin_from_github.is_on_actionbar)
        self.assertSetEqual(
            set(release.version for release in self.plugin_from_github.releases),
            {Version("1.0.0"), Version("1.1.0"), Version("1.2.2")})
        self.assertEqual(self.plugin_from_github.status, PluginStatus.NOT_INSTALLED)
        self.assertIsNone(self.plugin_from_github.installed_version)
        self.assertIsNone(self.plugin_from_github.installed_date)
        self.assertSetEqual(self.plugin_from_github.installed_files, set())
        self.assertIsNone(self.plugin_from_github.location)

        self.assertIsInstance(self.plugin_from_github.latest_compatible_release.allep_package, AllepPackage)


    def test_plugin_from_manifest_data(self):
        """Test creating a Plugin object from manifest data."""
        self.assertEqual(self.installed_plugin.uuid, UUID(self.installed_plugin_data["UUID"]))
        self.assertEqual(self.installed_plugin.name, self.installed_plugin_data["pluginName"])
        self.assertEqual(self.installed_plugin.installed_version, Version(self.installed_plugin_data["version"]))
        self.assertEqual(self.installed_plugin.installed_date, datetime.fromisoformat(self.installed_plugin_data["createdOn"]))

        self.assertIsInstance(self.installed_plugin.developer, Developer)
        self.assertEqual(len(self.installed_plugin.installed_files), 7)
        self.assertFalse(self.installed_plugin.has_github)
        self.assertTrue(self.installed_plugin.is_on_actionbar)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_fetched_plugin(self, _):
        """Test fetching attributes from another plugin."""
        self.plugin_from_github.fetch(self.installed_plugin)

        # Developer name from github should take precedence
        self.assertEqual(self.plugin_from_github.developer, self.plugin_github_data["developer"])

        self.assertEqual(self.plugin_from_github.name, self.installed_plugin_data["pluginName"])
        self.assertEqual(self.plugin_from_github.installed_version, Version(self.installed_plugin_data["version"]))
        self.assertEqual(self.plugin_from_github.installed_date, datetime.fromisoformat(self.installed_plugin_data["createdOn"]))
        self.assertEqual(len(self.installed_plugin.installed_files), 7)
        self.assertTrue(self.plugin_from_github.is_on_actionbar)
        self.assertTrue(self.plugin_from_github.has_github)

        self.plugin_from_github.check_releases()

        self.assertIsNotNone(self.plugin_from_github.latest_compatible_release)
        self.assertEqual(self.plugin_from_github.latest_compatible_release.version, Version("1.1.0"))
        self.assertSetEqual(
            set(release.version for release in self.plugin_from_github.releases),
            {Version("1.0.0"), Version("1.1.0"), Version("1.2.2")})
        self.assertEqual(self.plugin_from_github.status, PluginStatus.UPDATE_AVAILABLE)
