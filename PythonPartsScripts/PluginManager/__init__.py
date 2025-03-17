"""Module with entry point functions """
from .script_objects import PluginManagerScript


def check_allplan_version(_build_ele, version) -> bool:
    """ Check the current Allplan version

    Args:
        _build_ele: building element with the parameter properties
        version:    the current Allplan version

    Returns:
        True
    """

    # Supports only ALLPLAN 2026
    return float(version) >= 2026.0


def create_script_object(build_ele, script_object_data):
    """ Creation of the script object

    Args:
        build_ele:          building element with the parameter properties
        script_object_data: script object data

    Returns:
        created script object
    """

    return PluginManagerScript(build_ele, script_object_data)
