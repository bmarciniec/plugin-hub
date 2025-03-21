import unittest

from unittest.mock import patch
from uuid import UUID

from PluginManager.plugins import Plugin, PluginsCollection, PluginStatus
from PluginManager.site_libraries.packaging.specifiers import SpecifierSet
from PluginManager.site_libraries.packaging.version import Version

from tests.mocks import mocked_requests_get


class TestPluginsCollection(unittest.TestCase):

    def setUp(self):
        with patch('requests.get', side_effect=mocked_requests_get):
            self.plugins_collection = PluginsCollection()


    def test_append_new_plugin(self):
        """Test appending a new plugin to the collection."""
        size_before = len(self.plugins_collection)
        plugin = Plugin(
            uuid=UUID('52686573-ac50-47da-9426-96e0db791b96'),
            name='Test Plugin',
            developer='Developer Name'
        )
        self.plugins_collection.append(plugin)
        self.assertEqual(len(self.plugins_collection), size_before + 1)
        self.assertIsNone(plugin.github)
        self.assertEqual(plugin.status, PluginStatus.NOT_INSTALLED)


    @patch('requests.get', side_effect=mocked_requests_get)
    def test_append_existing_plugin(self, mock_requests_get):

        self.plugins_collection.get_plugins_from_github()

        size_before = len(self.plugins_collection)
        plugin = Plugin(
            uuid=UUID('c9bf9e57-1685-4c89-bafb-ff5af830be8a'),
            name='Test Plugin',
            developer='Different Developer Name',
            github={
                "owner": "owner",
                "repo": "repo"
            }
        )
        self.plugins_collection.append(plugin)

        # size should not increase
        self.assertEqual(len(self.plugins_collection), size_before)

        # because the plugin is registered in GitHub, its developer name should also not change
        self.assertEqual(
            self.plugins_collection[UUID("c9bf9e57-1685-4c89-bafb-ff5af830be8a")].developer.id,
            'another-developer')
        self.assertIsNotNone(plugin.github)
        self.assertEqual(plugin.status, PluginStatus.NOT_INSTALLED)


    @patch('requests.get', side_effect=mocked_requests_get)
    def test_plugin_without_compatibility_specifier(self, mock_requests_get):
        self.plugins_collection.get_plugins_from_github()

        # get the plugin "Example Plugin 3"
        plugin = self.plugins_collection[UUID("e7d3e8e2-8b2d-4d8d-8b2d-4d8d8b2d4d8d")]
        self.assertEqual(plugin.name, "Example Plugin 3")
        self.assertIsNone(plugin.compatibility)
        self.assertEqual(len(plugin.releases), 6)
        self.assertEqual(plugin.latest_compatible_release.version, Version("2.1.6"))


    @patch('requests.get', side_effect=mocked_requests_get)
    def test_plugin_with_compatibility_specifier(self, mock_requests_get):
        self.plugins_collection.get_plugins_from_github()

        # get the plugin Example Plugin 4
        plugin = self.plugins_collection[UUID("a3bb189e-8bf9-3888-9912-ace4e6543002")]
        self.assertEqual(plugin.name, "Example Plugin 4")
        self.assertEqual(plugin.developer.id, "example-developer")
        self.assertEqual(plugin.compatibility, SpecifierSet("~=1.0"))
        self.assertEqual(len(plugin.releases), 3)
        self.assertEqual(plugin.latest_compatible_release.version, Version("1.1.0"))

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_plugins_from_github_and_installed(self, mock_requests_get):

        self.plugins_collection.get_plugins_from_github()
        self.plugins_collection.get_installed_plugins()

        self.assertEqual(len(self.plugins_collection), 5)

        self.assertSetEqual(
            {plugin.name for plugin in self.plugins_collection},
            {"Example Plugin 1", "Example Plugin 2", "Example Plugin 3", "Example Plugin 4", "Plugin not registered on GitHub"})

        self.assertListEqual(
            list(plugin.name for plugin in self.plugins_collection),
            ["Example Plugin 1",
             "Example Plugin 2",
             "Example Plugin 3",
             "Example Plugin 4",
             "Plugin not registered on GitHub"])

        self.assertListEqual(
            list(plugin.status for plugin in self.plugins_collection),
            [PluginStatus.NOT_INSTALLED,
             PluginStatus.UPDATE_AVAILABLE,
             PluginStatus.NOT_INSTALLED,
             PluginStatus.UPDATE_AVAILABLE,
             PluginStatus.INSTALLED])

        self.assertListEqual(
            list(plugin.has_github for plugin in self.plugins_collection),
            [True, True, True, True, False])

        self.assertRaises(RuntimeError, lambda: self.plugins_collection[4].latest_compatible_release)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_plugins_from_github(self, mock_requests_get):
        self.plugins_collection.get_plugins_from_github()

        # one plugin comes from non-existing developer, so expected is 4, not 5
        self.assertEqual(len(self.plugins_collection), 4)

        self.assertSetEqual(
            {developer.id for developer in self.plugins_collection.developers},
            {"some-developer", "another-developer", "example-developer"})

        self.assertListEqual(
            list(plugin.name for plugin in self.plugins_collection),
            ["Example Plugin 1",
             "Example Plugin 2",
             "Example Plugin 3",
             "Example Plugin 4"])

        self.assertTrue(all(plugin.has_github for plugin in self.plugins_collection))
        self.assertTrue(all(plugin.latest_compatible_release is not None for plugin in self.plugins_collection))
        self.assertListEqual(
            list(plugin.latest_compatible_release.version for plugin in self.plugins_collection),
            [Version("2.1.6"),
             Version("2.1.6"),
             Version("2.1.6"),
             Version("1.1.0"), # this plugin has compatibility specifier
             ])

        self.assertTrue(all(plugin.latest_compatible_release.allep_package is not None for plugin in self.plugins_collection))
