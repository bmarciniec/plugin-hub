import json
import unittest

from unittest.mock import patch
from uuid import UUID

from PythonPartsScripts.PluginManager.developers import Developer
from PythonPartsScripts.PluginManager.plugins import Plugin, PluginsCollection, PluginStatus
from PythonPartsScripts.PluginManager.releases import Releases
from PythonPartsScripts.PluginManager.site_libraries.packaging.specifiers import SpecifierSet
from PythonPartsScripts.PluginManager.site_libraries.packaging.version import Version


class TestPluginsCollection(unittest.TestCase):

    def setUp(self):

        with open("tests/test_data/allplan-extensions.json") as f:
            self.plugins_data = json.load(f)

        with open("tests/test_data/plugin-developers.json") as f:
            self.developers_data = json.load(f)

        with open("tests/test_data/releases.json") as f:
            self.releases_data = json.load(f)

        with patch('requests.get') as mock_requests_get:
            mock_requests_get.return_value.json.return_value = self.developers_data
            self.plugins_collection = PluginsCollection()

    @patch('requests.get')
    def test_get_plugins_from_github(self, mock_requests_get):
        mock_requests_get.return_value.json.return_value = self.plugins_data
        self.plugins_collection.get_plugins_from_github()

        # one plugin comes from non-existing developer
        self.assertLess(len(self.plugins_collection), len(self.plugins_data))

        self.assertEqual(
            first={developer.id for developer in self.plugins_collection.developers},
            second={developer["id"] for developer in self.developers_data})

    def test_append_new_plugin(self):
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

    @patch('requests.get')
    def test_append_existing_plugin(self, mock_requests_get):
        mock_requests_get.return_value.json.return_value = self.plugins_data

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
            first=self.plugins_collection[UUID("c9bf9e57-1685-4c89-bafb-ff5af830be8a")].developer.id,
            second='another-developer')
        self.assertIsNotNone(plugin.github)
        self.assertEqual(plugin.status, PluginStatus.NOT_INSTALLED)


    @patch('requests.get')
    def test_plugin_with_compatibility_specifier(self, mock_requests_get):
        mock_requests_get.return_value.json.return_value = self.plugins_data

        self.plugins_collection.get_plugins_from_github()

        plugin = self.plugins_collection[UUID("a3bb189e-8bf9-3888-9912-ace4e6543002")]

        self.assertIsInstance(plugin.compatibility, SpecifierSet)


        mock_requests_get.return_value.json.return_value = self.releases_data
        self.assertIsInstance(plugin.releases, set)
        self.assertEqual(plugin.latest_compatible_release.version, Version("1.1.0"))
        self.assertEqual(len(plugin.releases), 3)


    # @patch('Pluginmanager.plugins.Path.exists')
    # @patch('Pluginmanager.plugins.open', new_callable=unittest.mock.mock_open, read_data='{"plugins": []}')
    # def test_get_installed_plugins(self, mock_open, mock_path_exists):
    #     mock_path_exists.return_value = True
    #     self.plugins_collection.get_installed_plugins()
    #     self.assertEqual(len(self.plugins_collection), 0)

    # def test_update_building_element(self):
    #     mock_building_element = MagicMock()
    #     plugin = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='Test Plugin',
    #         developer=Developer(name='Developer 1')
    #     )
    #     self.plugins_collection.append(plugin)
    #     self.plugins_collection.update_building_element(mock_building_element)
    #     mock_building_element.PluginStates.value = [plugin.status for plugin in self.plugins_collection]

    # def test_clean_up(self):
    #     plugin = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='Test Plugin',
    #         developer=Developer(name='Developer 1'),
    #         github=None
    #     )
    #     self.plugins_collection.append(plugin)
    #     self.plugins_collection.clean_up()
    #     self.assertEqual(len(self.plugins_collection), 0)

    # def test_sort_plugins(self):
    #     plugin1 = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='B Plugin',
    #         developer=Developer(name='Developer 1')
    #     )
    #     plugin2 = Plugin(
    #         uuid=UUID('87654321-4321-8765-4321-876543218765'),
    #         name='A Plugin',
    #         developer=Developer(name='Developer 2')
    #     )
    #     self.plugins_collection.append(plugin1)
    #     self.plugins_collection.append(plugin2)
    #     self.plugins_collection._sort_plugins()
    #     self.assertEqual(self.plugins_collection._sorted_uuids, [plugin2.uuid, plugin1.uuid])

    # def test_getitem(self):
    #     plugin = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='Test Plugin',
    #         developer=Developer(name='Developer 1')
    #     )
    #     self.plugins_collection.append(plugin)
    #     self.assertEqual(self.plugins_collection[plugin.uuid], plugin)

    # def test_iter(self):
    #     plugin1 = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='B Plugin',
    #         developer=Developer(name='Developer 1')
    #     )
    #     plugin2 = Plugin(
    #         uuid=UUID('87654321-4321-8765-4321-876543218765'),
    #         name='A Plugin',
    #         developer=Developer(name='Developer 2')
    #     )
    #     self.plugins_collection.append(plugin1)
    #     self.plugins_collection.append(plugin2)
    #     plugins = list(self.plugins_collection)
    #     self.assertEqual(plugins, [plugin2, plugin1])

    # def test_len(self):
    #     plugin = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='Test Plugin',
    #         developer=Developer(name='Developer 1')
    #     )
    #     self.plugins_collection.append(plugin)
    #     self.assertEqual(len(self.plugins_collection), 1)

    # def test_repr(self):
    #     plugin = Plugin(
    #         uuid=UUID('12345678-1234-5678-1234-567812345678'),
    #         name='Test Plugin',
    #         developer=Developer(name='Developer 1')
    #     )
    #     self.plugins_collection.append(plugin)
    #     self.assertEqual(repr(self.plugins_collection), f"PluginsCollection({self.plugins_collection._plugins})")

if __name__ == '__main__':
    unittest.main()