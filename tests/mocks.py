import importlib
import json

from unittest.mock import Mock


# Function to mock requests.get
def mocked_requests_get(url, *args, **kwargs):
    """Mock the requests.get function to return predefined responses.

    Args:
        url: The URL of the request.

    Returns:
        A mock response object.
    """
    # Create a mock response object
    mock_response = Mock()
    config = importlib.import_module("PluginManager.config")

    # Define different responses based on the URL
    if url.endswith("/releases/latest"):
        with open("tests/test_data/latest-release.json", encoding="utf-8") as f:
            mock_response.json.return_value = json.load(f)

    elif url.endswith("/releases"):
        with open("tests/test_data/releases.json", encoding="utf-8") as f:
            mock_response.json.return_value = json.load(f)
            mock_response.status_code = 200

    elif url == config.EXTENSIONS_URL:
        with open("tests/test_data/allplan-extensions.json", encoding="utf-8") as f:
            mock_response.json.return_value = json.load(f)
            mock_response.status_code = 200

    elif url == config.DEVELOEPERS_URL:
        with open("tests/test_data/plugin-developers.json", encoding="utf-8") as f:
            mock_response.json.return_value = json.load(f)
            mock_response.status_code = 200

    return mock_response

class PathConstantsMock(str):
    ETC_PATH = "etc"
    STD_PATH = "std"
    USR_PATH = "usr"
    PRJ_PATH = "prj"

    PATH_KEYS_SEARCH_ORDER = (PRJ_PATH, STD_PATH, ETC_PATH, USR_PATH)

    PYP_SEARCH_PATHS = ("tests\\test_data\\prj\\",
                        "tests\\test_data\\std\\",
                        "tests\\test_data\\etc\\",
                        "tests\\test_data\\usr\\")

    KEY_PATH_TUPLES = ((ETC_PATH, "tests\\test_data\\etc\\"),
                       (STD_PATH, "tests\\test_data\\std\\"),
                       (USR_PATH, "tests\\test_data\\usr\\"),
                       (PRJ_PATH, "tests\\test_data\\prj\\"))


# class AllplanPathsMock():

#     @staticmethod
#     def GetUsrPath() -> str:
#         return "tests\\test_data\\usr"

#     @staticmethod
#     def GetStdPath() -> str:
#         return "tests\\test_data\\std"

#     @staticmethod
#     def GetEtcPath() -> str:
#         return "tests\\test_data\\etc"
