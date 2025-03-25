"""Utility class for reading yaml file."""

import os
import subprocess

from pathlib import Path
from xml.etree import ElementTree as ET

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_Utility as AllPlanUtility

from pydantic import BaseModel, Field, validator

LOCATION         = Path(__file__)
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))

DOCTYPE = (
    '<?xml version="1.0" encoding="utf-8"?><!DOCTYPE Plugin SYSTEM "..\\Plugin.dtd" []>'
)
NAMESPACE = "http://www.w3.org/XML/1998/namespace"





DOCTYPE          = '<?xml version="1.0" encoding="utf-8"?><!DOCTYPE Plugin SYSTEM "..\\Plugin.dtd" []>'
DOCTYPE_ACTB     = '<?xml version="1.0" encoding="utf-8"?>'
INVALID_CHARS    = ("<", ">", ":", '"', "/", "\\", "|", "?")


def sanitize_strings(value: str) -> str:
    """ Sanitize strings to conform to winodws file naming conventions.

    Args:
        value: String value.

    Returns:
        str: sanitied string.
    """

    for c in INVALID_CHARS:
        value = value.replace(c, "-")
    value = value.replace(" ","")
    return value

class Base(BaseModel):
    """base class for yaml elements"""

    @classmethod
    def append_path(cls, file: str, path: str) -> str:
        """Append directory folder to file path.

        Args:
            file (str): File name.
            path (str)  : Path of directory.

        Returns:
            str: full path of object.
        """
        return f"{path}\\{file}"

    class Config:
        """Config class for Base Model"""

        extra = "allow"


class Plugins(Base):
    """Class to serialize plugin data from config.yml"""

    name         : str
    developer    : str
    UUID         : str
    version      : str
    min_version  : int = Field(alias= "min-allplan-version")
    default_lang : str = Field(alias= "default-language")

    def __init__(self, *args, **kwargs):

        """Init function of the plugin class."""

        super().__init__(*args, **kwargs)

        self.original_name = kwargs["name"]
        self.original_developer_name = kwargs["developer"]


    @validator("name", "developer")
    def validate_strings(cls, value: str):
        return sanitize_strings(value)

    def get_folder_name(self) -> str:
        """ Return folder name

        Returns:
            str: Name of folder.
        """

        return f"{self.developer}.{self.name}"

class Icons(Base):
    """Class to serialize images from config.yml"""

    small: str
    large: str

class PythonScripts(Base):
    """Class to serialize tools from config.yml"""

    id: str
    script: str  = Field(alias="pyp")
    icons: Icons
    display_name: dict[str, str] = Field(alias="display-name")


class TaskArea(BaseModel):
    """Class to serialize Task area model."""

    display_name : dict[str, str] = Field(alias="display-name")
    container    : list[str]      = Field(alias="layout")


class Installation(Base):
    """Class to serialize Installation model."""

    target_location    : str           = Field(alias="target-location")
    py_packages        : (str | None ) = Field(alias="py-packages", default=None)
    pythonpart_scripts : (str | None ) = Field(alias="PythonPartsScripts", default="PythonPartsScripts")
    actionbar          : (str | None ) = Field(alias="PythonPartsActionbar", default="PythonPartsActionbar")
    library            : (str | None ) = Field(alias="Library", default="Library")

    def __init__(self, **kwargs):
        """init function
        Args:
            **kwargs: Keyword arguments.
        """

        if kwargs["target-location"] is None:
            raise KeyError("The target-location cannot be Empty and must be a string.")

        kwargs["target-location"]      = kwargs.get("target-location", "").capitalize()

        super().__init__(**kwargs)

    def get_update_target_location(self):
        if not hasattr(self, "update_target_location"):
            temp  = self.get_path_function().split("\\")
            index = [i for i in range(len(temp)) if self.target_location in temp[i] or self.target_location == temp[i]][0]
            self.update_target_location = "\\".join(temp[index:-1])

        return self.update_target_location

    def get_path_function(self) -> str:

        """ Get path funtion

        Returns:
            Callable: Returns athe valid path funtion.
        """

        if self.target_location == "Etc":
            return AllplanSettings.AllplanPaths.GetEtcPath()

        if self.target_location == "Std":
            return AllplanSettings.AllplanPaths.GetStdPath()

        return AllplanSettings.AllplanPaths.GetUsrPath()

    def get_install_location(self) -> str:

        """Get valid install location for plugins.

        Returns:
            str: Full path of allep plugins.
        """

        return f"{self.get_path_function()}PythonPartsActionbar"

    def install_pypackages(self, require_file: (str | None) = None):
        """Install packages from py_packages

        Args:
            require_file: Destination of requirement.in file.
        """
        if not self.py_packages :
            return

        prg_path = AllplanSettings.AllplanPaths.GetPrgPath() + "\\"

        if self.target_location == "Etc":
            path_function = AllplanSettings.AllplanPaths.GetPythonPartsEtcPath

        elif self.target_location == "Std":
            path_function = AllplanSettings.AllplanPaths.GetStdPath

        elif self.target_location == "Usr":
            path_function = AllplanSettings.AllplanPaths.GetUsrPath

        target_dir   = f"{path_function()}PythonParts-site-packages"
        require_file = self.py_packages if require_file is None else require_file

        try:
            subprocess.check_call(
                [
                    f"{prg_path}Python\\Python.exe",
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    f"{require_file}",
                    "--target",
                    target_dir,
                    "--no-cache-dir",
                ]
            )
        except Exception as exc:
            raise ValueError("Unable to install py packages.") from exc


class AppConfig(Base):
    """Helper class to read yml config"""

    tools: (list[PythonScripts] | None) = None
    plugin: Plugins
    task_area: (TaskArea | None) = Field(alias="task-area", default= None)
    installation: Installation


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.tools_by_id = {}
        if self.tools:
            for x in self.tools:
                self.tools_by_id[x.id] = x

    def get_icon_path(self, icon):
        return f"{self.installation.target_location}\\PythonPartsActionbar\\{icon}"

    def _get_string_table( self, node: ET.Element, language: str | None = None ) -> list[ET.Element]:
        """Get string table

        Args:
            node     : Root of XML.
            language : The language of string table.

        Returns:
            list     : list of StringTables.
        """
        string_tables = node.findall("StringTable")
        namespace     = "{" + NAMESPACE + "}" + "lang"

        if language:
            return [x for x in string_tables if x.attrib[namespace] == language]

        return string_tables


    def get_file_location(self) -> str:
        """Returns the full path of actb or npd file with name.

        Return:
            str: The full path of actb or npd file with name.

        """

        return f"{self.installation.get_install_location()}\\{self.plugin.UUID}"

    def _create_string_table(self, node: ET.Element, language: str) -> ET.Element:
        """Create a string table.

        Args:
            node     : Node of XML table.
            language : Language of String table.

        Returns:
            ET.Element: _description_
        """

        string_table = self._get_string_table(node, language)
        namespace    = "{" + NAMESPACE + "}" + "lang"

        if len(string_table) == 0:
            string_table = ET.SubElement(
                node, "StringTable", attrib={namespace: language}
            )
            return string_table

        return string_table[0]

    def add_value_string_table(self, value: str, ids: str, string_table: ET.Element):
        """Add text element to string table.

        Args:
            value : Value to add in string table.
            lang  : Language of string table.
            ids   : Id of related element.
        """

        text_element      = ET.SubElement(string_table, "text", attrib={"ids": ids})
        text_element.text = value

    def create_button(
        self,
        script: PythonScripts,
        toolbar: ET.Element,
        node: ET.Element,
        event_id: str,
        localisation_id: str,
    ):
        """Create buttons in npd file.

        Args:
            script          : Script of tool.
            toolbar         : Toolbar element.
            node            : Root element.
            event_id        : Event id of button.
            localisation_id : localisation id.
        """
        icon_path   = f"{self.installation.target_location}\\PythonPartsActionbar"
        script_path = f"{self.installation.target_location}\\Library"
        attrs = {
            "id": event_id,
            "Path": f"{script_path}\\{script.script}",
            "EnabledIn": "FILE",
            "NameIDS": localisation_id,
            "Bitmap16IDB": f"{icon_path}\\{script.icons.small}",
            "Bitmap24IDB": f"{icon_path}\\{script.icons.large}",
        }

        # rector this into a separate function
        for language, value in script.display_name.items():
            string_table = self._create_string_table(node, language)
            self.add_value_string_table(value, localisation_id, string_table)

        _ = ET.SubElement(toolbar, "Button", attrib=attrs)
        script.name_id = localisation_id
        script.event_id = event_id

    def create_npd_file(self) -> ET.Element:
        """Create npd file from config.

        Returns:
            ET.Element: Root element of npm file.
        """

        template_xml = ET.parse(LOCATION.with_name("npd_template.tmpl"))
        node = template_xml.getroot()

        # Update plugin propertirs and add value to string table.
        plugin_pro = node.findall("PluginProperties")[0]
        plugin_pro.attrib["UUID"] = self.plugin.UUID


        # Add Group and Task into string table
        if self.task_area:
            for language, value in self.task_area.display_name.items():
                string_table = self._create_string_table(node, language)
                self.add_value_string_table(value, "0010", string_table)
                self.add_value_string_table(self.plugin.original_name, "100", string_table)

        if not self.task_area:
            string_table = self._create_string_table(node, self.plugin.default_lang)
            self.add_value_string_table(self.plugin.name, "0010", string_table)
            self.add_value_string_table(self.plugin.original_name, "100", string_table)


        # Update model group and add images.
        model_group = node.findall("ModuleGroup")[0]
        model_group.attrib["Bitmap16IDB"] = self.get_icon_path( self.tools[0].icons.small)
        model_group.attrib["Bitmap24IDB"] = self.get_icon_path( self.tools[0].icons.large)

        # Update model
        model = model_group.find("Module")
        model.attrib["Bitmap16IDB"] = self.get_icon_path( self.tools[0].icons.small)
        model.attrib["Bitmap24IDB"] = self.get_icon_path( self.tools[0].icons.large)

        # Add scripts tools
        toolbar = model.find("Toolbar")
        localisation_id = 310
        event_id = 3410
        for x in self.tools:
            self.create_button(x, toolbar, node, str(event_id), str(localisation_id))  # type: ignore
            event_id = event_id + 1
            localisation_id = localisation_id + 1
        return node

    def create_actb_file(self) -> ET.Element:
        """ Create actb file from config

        Returns:
            bool: Bool value to represent file creation state.
        """

        template_xml = ET.parse(LOCATION.with_name("actb_template.actb"))
        node         = template_xml.getroot()

        # Add attribs
        node.attrib["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"
        node.attrib["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"

        # Role
        role      = node.find("Role")
        name      = role.findall("Name")[0]
        name.text = self.plugin.name

        # Add UUID To Task

        task_tag  = role.find("Task")
        uuid      = task_tag.find("UUID")
        uuid.text = self.plugin.UUID

        # Add NameID in group
        npd_hash                = AllPlanUtility.GetPluginNameHash(f"{self.installation.get_update_target_location()}\\PythonPartsActionbar\\{self.plugin.UUID}.npd")
        group                   = task_tag.find("Group")
        group.find("NameID").text = f"PLUGIN_||10||{self.plugin.name}#{npd_hash}"

        # Create FlyOuts
        container = group.find("Container")

        for index, item  in enumerate(self.task_area.container):

            if "**" in item and index not in (0, len(self.task_area.container)-1):
                container = ET.SubElement(group, "Container",)

            elif "--" in item and index not in (0, len(self.task_area.container)-1):
                flyout     = ET.SubElement(container,"FlyOut",)
                event      = ET.SubElement(flyout, "Event",)
                event.text = "SEPARATOR - -"

            else:
                flyout     = ET.SubElement(container,"FlyOut",)
                event      = ET.SubElement(flyout, "Event",)
                if item in self.tools_by_id:
                    event.text = f"PLUGIN_||{self.tools_by_id[item].event_id}||{self.plugin.name}#{npd_hash} - {self.tools_by_id[item].display_name['en']}"
        return node

    def write_file(self):

        if self.tools:
            node      = self.create_npd_file()
            tree_node = ET.ElementTree(node)

            os.makedirs(f"{self.installation.get_install_location()}", exist_ok=True)

            with open(f"{self.get_file_location()}.npd", "wb") as node_file:
                node_file.write(DOCTYPE.encode("utf8"))
                tree_node.write(node_file, "utf-8")


        if self.tools and self.task_area:
            node      = self.create_actb_file()
            tree_node = ET.ElementTree(node)

            with open(f"{self.get_file_location()}.actb", "wb") as node_file:
                node_file.write(DOCTYPE_ACTB.encode("utf8"))
                tree_node.write(node_file, 'utf-8')


if __name__ == "__main__":
    pass
