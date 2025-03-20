"""Tests for the releases module."""
import datetime
import json
import unittest

from unittest.mock import patch

from PythonPartsScripts.PluginManager.allep import AllepPackage
from PythonPartsScripts.PluginManager.releases import Release, Releases
from PythonPartsScripts.PluginManager.site_libraries.packaging import specifiers, version


class TestRelease(unittest.TestCase):

    def setUp(self):
        with open("tests/test_data/releases.json") as f:
            self.releases = json.load(f)

    def test_from_github(self):
        release = Release.from_github_data(self.releases[1])
        self.assertEqual(release.version.major, 1)
        self.assertEqual(release.version.minor, 0)
        self.assertEqual(release.published_at.date(), datetime.date(2023, 2, 1))
        self.assertEqual(release.url, "https://github.com/example-owner4/example-repo4/releases/1.0.0")
        self.assertFalse(release.is_prerelease)
        self.assertIsInstance(release.allep_package, AllepPackage)
        self.assertEqual(release.allep_package.name, "plugin.allep")

    def test_from_github_no_assets(self):
        release = self.releases[1]
        release["assets"] = []
        with self.assertRaises(ValueError):
            Release.from_github_data(release)

    def test_from_github_no_allep_package(self):
        release = self.releases[2]
        release["assets"][0]["name"] = "plugin.zip"
        with self.assertRaises(ValueError):
            Release.from_github_data(release)


class TestReleases(unittest.TestCase):

    def setUp(self):
        with open("tests/test_data/releases.json") as f:
            self.releases_data = json.load(f)

        self.releases = Releases()

        for release_data in self.releases_data:
            release = Release.from_github_data(release_data)
            self.releases.add(release)

    def test_add_release(self):
        release = Release.from_github_data(self.releases_data[0])
        releases = Releases()
        releases.add(release)
        self.assertIn(release, releases)

    def test_add_invalid_release(self):
        with self.assertRaises(ValueError):
            self.releases.add("lolwat")

    def test_get_matching(self):
        specifier = specifiers.SpecifierSet("~=1.0")
        matching_releases = self.releases.get_matching(specifier)
        matching_release_versions = {release.version for release in matching_releases}
        self.assertIn(version.parse("v1.0.0"), matching_release_versions)
        self.assertIn(version.parse("v1.1.0"), matching_release_versions)
        self.assertNotIn(version.parse("v1.2.2"), matching_release_versions)

    def test_get_matching_including_prerelease(self):
        specifier = specifiers.SpecifierSet("~=1.0")
        matching_releases = self.releases.get_matching(specifier, True)
        matching_release_versions = {release.version for release in matching_releases}
        self.assertIn(version.parse("v1.2.2"), matching_release_versions)

    def test_get_latest_matching(self):
        specifier = specifiers.SpecifierSet("~=2.0")
        latest_release = self.releases.get_latest_matching(specifier)
        self.assertEqual(latest_release.version, version.parse("2.1.6"))

    @patch('requests.get')
    def test_get_latest_from_github(self, mock_get):
        mock_get.return_value.json.return_value = self.releases_data[-2]
        mock_get.return_value.raise_for_status = lambda: None
        latest_release = Releases._get_latest_from_github("owner", "repo")
        self.assertEqual(latest_release.version, version.parse("2.1.6"))

def test_releases():
    unittest.main()
