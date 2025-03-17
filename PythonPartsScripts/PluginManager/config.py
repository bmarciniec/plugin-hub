"""Module with configuration constants for the ExtensionHub package."""
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    # "Authorization": "Bearer <YOUR-TOKEN>",
    "X-GitHub-Api-Version": "2022-11-28"
}

class PluginHubRepo:
    """Class with constants for the Plugin Hub repository."""
    OWNER  = 'bmarciniec'
    REPO   = 'plugin-hub'
