"""Module with configuration constants for the ExtensionHub package."""

import NemAll_Python_AllplanSettings as AllplanSettings


class PluginHubRepo:
    """Class with constants for the Plugin Hub repository."""
    OWNER  = 'bmarciniec'
    REPO   = 'plugin-hub'
    BRANCH = 'main' if AllplanSettings.AllplanVersion.MainReleaseName() == "9999" else AllplanSettings.AllplanVersion.MainReleaseName()

GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    # "Authorization": "Bearer <YOUR-TOKEN>",
    "X-GitHub-Api-Version": "2022-11-28"
}

EXTENSIONS_URL = f'https://raw.githubusercontent.com/{PluginHubRepo.OWNER}/{PluginHubRepo.REPO}/{PluginHubRepo.BRANCH}/allplan-extensions.json'
DEVELOEPERS_URL = f'https://raw.githubusercontent.com/{PluginHubRepo.OWNER}/{PluginHubRepo.REPO}/{PluginHubRepo.BRANCH}/plugin-developers.json'
