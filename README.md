# ALLPLAN Plugin Hub

ALLPLAN Plugin Hub is a PythonPart script to help you find and install all available plugins which runs on ALLPLAN and belongs to ALLPLAN.

## Installation
To install the ALLPLAN Plugin Hub:
1. Download the zip file from this repo and unpack it
1. Start *add_to_allplan.bat* with the option **Run as administrator**
1. Copy the `STD` path of your ALLPLAN 2026 WIP or ALLPLAN MAIN codeline (with trailing backslash `\`, e.g.: `C:\Data\Allplan\Allplan 2026\Std\`)
1. Press `i` and paste the path
1. (Re)start ALLPLAN and go to `Library` → `Office` → `Content` → `Plugin Hub`
1. Start the **Plugin Hub** from there

## Uninstallation
To remove the ALLPLAN Plugin Hub:
1. Start *add_to_allplan.bat* again with the option **Run as administrator**
2. Press `r` and paste the `STD` path again

## Submit Your Plugin
### Step 1:
Prepare a GitHub repo to host your `ALLEP` file as part of a release:
1. Use your ALLPLAN account to create an account on GitHub
1. Create a **public** repo
1. Create a release for your repo
    1. Provide your `ALLEP` file as part of the release.
    1. Make sure the name of the release is equal to the version of the one in the file *install-config.yml*.
    1. Make sure to set the latest release correctly, if needed.

### Step 2:
Make a pull request to this repo, which modifies the file *allplan-extensions.json* to include following information for your plugin:

```json
[
    {
        "uuid": "plugin uuid in the install-config.yml",
        "name": "Plugin Name",
        "developer": "Developer Name",
        "description": "One line short description for the plugin.",
        "github": {
            "owner": "your-github-username",
            "repo": "your-repo-name"
        }
    }
]
```

After we review and approve your pull request, your plugin will show up automatically when you start the *Plugin Hub* next time. You don't need to make a pull request if you update your plugin, unless you want to change the information available in this `json` file.