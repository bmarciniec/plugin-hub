<?xml version="1.0" encoding="utf-8"?>
<Element xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:noNamespaceSchemaLocation="https://pythonparts.allplan.com/2026/schemas/PythonPart.xsd">
  <Script>
    <Name>PluginManager.py</Name>
    <Title>ALLPLAN Plugin Manager</Title>
    <Version>0.1</Version>
  </Script>
  <Constants>
    <!-- Actions -->
    <Constant>
      <Name>INSTALL</Name>
      <Value>1001</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>CHECK_FOR_UPDATES</Name>
      <Value>1002</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>UPDATE</Name>
      <Value>1003</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>SHOW_DETAILS</Name>
      <Value>1004</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>UNINSTALL</Name>
      <Value>1005</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>EMAIL_TO_SUPPORT</Name>
      <Value>1006</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>GO_TO_HOMEPAGE</Name>
      <Value>1007</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <!-- Palette states -->
    <Constant>
      <Name>SHOW_OVERVIEW</Name>
      <Value>2001</Value>
      <ValueType>Integer</ValueType>
    </Constant>
    <Constant>
      <Name>SHOW_DETAILS</Name>
      <Value>2002</Value>
      <ValueType>Integer</ValueType>
    </Constant>
  </Constants>
  <Page>
    <Name>PluginOverview</Name>
    <Text>Plugin overview</Text>
    <Visible>CurrentPaletteState == SHOW_OVERVIEW</Visible>
    <Parameters>
      <Parameter>
        <Name>PluginListGroup</Name>
        <ValueType>ListGroup</ValueType>
        <Parameters>
          <Parameter>
            <Name>TitleRow</Name>
            <Text>Foo</Text>
            <ValueType>Row</ValueType>
            <Value>OVERALL</Value>
            <Parameters>
              <Parameter>
                <Name>PluginNames</Name>
                <Text>Foo</Text>
                <Orientation>Left</Orientation>
                <Value>[_]</Value>
                <ValueType>Text</ValueType>
                <FontFaceCode>1</FontFaceCode>
                <FontStyle>4</FontStyle>
              </Parameter>
              <Parameter>
                <Name>DetailsButton</Name>
                <Text>Show the plugin details</Text>
                <EventId>SHOW_DETAILS</EventId>
                <Value>AllplanSettings.PictResPalette.eHotinfo</Value>
                <ValueType>PictureResourceButton</ValueType>
                <WidthInRow>5</WidthInRow>
              </Parameter>
              <Parameter>
                <Name>InstallButton</Name>
                <Text>Download and install</Text>
                <EventId>INSTALL</EventId>
                <Value>8522</Value>
                <ValueType>PictureResourceButton</ValueType>
                <Visible>PluginStates[$list_row] == 0</Visible>
                <WidthInRow>5</WidthInRow>
              </Parameter>
              <Parameter>
                <Name>CheckForUpdatesButton</Name>
                <Text>Check for updates</Text>
                <EventId>CHECK_FOR_UPDATES</EventId>
                <Value>14057</Value>
                <ValueType>PictureResourceButton</ValueType>
                <Visible>PluginHasGitHubRepo[$list_row] and PluginStates[$list_row] == 1</Visible>
                <WidthInRow>5</WidthInRow>
              </Parameter>
              <Parameter>
                <Name>UpdateButton</Name>
                <Text>Update the plugin</Text>
                <EventId>UPDATE</EventId>
                <Value>8519</Value>
                <ValueType>PictureResourceButton</ValueType>
                <Visible>PluginStates[$list_row] == 2</Visible>
                <WidthInRow>5</WidthInRow>
              </Parameter>
              <Parameter>
                <Name>UpToDateButton</Name>
                <Text>Plugin is up to date</Text>
                <EventId>0</EventId>
                <Value>11433</Value>
                <ValueType>PictureResourceButton</ValueType>
                <Enable>False</Enable>
                <Visible>PluginStates[$list_row] == 3</Visible>
                <WidthInRow>5</WidthInRow>
              </Parameter>
              <Parameter>
                <Name>UninstallButton</Name>
                <Text>Uninstall this plugin</Text>
                <EventId>UNINSTALL</EventId>
                <Value>10051</Value>
                <ValueType>PictureResourceButton</ValueType>
                <Visible>PluginStates[$list_row] != 0</Visible>
                <WidthInRow>5</WidthInRow>
              </Parameter>
            </Parameters>

          </Parameter>

          <Parameter>
            <Name>DescriptionRow</Name>
            <Text>Bar</Text>
            <ValueType>Row</ValueType>
            <Value>OVERALL</Value>
            <Parameters>
              <Parameter>
                <Name>PluginDescriptions</Name>
                <Text />
                <Value>[_]</Value>
                <ValueType>Text</ValueType>
                <Visible>PluginDescriptions[$list_row] != ""</Visible>
                <FontStyle>1</FontStyle>
              </Parameter>
            </Parameters>
          </Parameter>
          <Parameter>
            <Name>Separator</Name>
            <ValueType>Separator</ValueType>
          </Parameter>
        </Parameters>
      </Parameter>
    </Parameters>
  </Page>

  <Page>
    <Name>PluginDetails</Name>
    <Text>Plugin details</Text>
    <Visible>CurrentPaletteState == SHOW_DETAILS</Visible>
    <Parameters>
      <Parameter>
        <Name>PluginExpander</Name>
        <Text>Plugin</Text>
        <Value>False</Value>
        <ValueType>Expander</ValueType>
        <Parameters>
          <Parameter>
            <Name>PluginUUID</Name>
            <Text>UUID</Text>
            <Value> </Value>
            <ValueType>Text</ValueType>
            <Visible>False</Visible>
          </Parameter>
          <Parameter>
            <Name>PluginName</Name>
            <Text>Name</Text>
            <Value> </Value>
            <ValueType>Text</ValueType>
          </Parameter>
          <Parameter>
            <Name>InstalledVersion</Name>
            <Text>Installed version</Text>
            <Value> </Value>
            <ValueType>Text</ValueType>
          </Parameter>
          <Parameter>
            <Name>InstallDate</Name>
            <Text>Installation date</Text>
            <Value> </Value>
            <ValueType>Text</ValueType>
          </Parameter>
          <Parameter>
            <Name>InstallLocation</Name>
            <Text>Installed in</Text>
            <Value> </Value>
            <ValueType>Text</ValueType>
          </Parameter>
        </Parameters>
      </Parameter>
      <Parameter>
        <Name>DeveloperExpander</Name>
        <Text>Developer</Text>
        <Value>False</Value>
        <ValueType>Expander</ValueType>
        <Parameters>
          <Parameter>
            <Name>DeveloperName</Name>
            <Text>Name</Text>
            <Value></Value>
            <ValueType>Text</ValueType>
          </Parameter>
          <Parameter>
            <Name>DeveloperAddress</Name>
            <Text>Address</Text>
            <Value></Value>
            <ValueType>Text</ValueType>
          </Parameter>
          <Parameter>
            <Name>DeveloperSupportRow</Name>
            <Text>Support</Text>
            <ValueType>Row</ValueType>
            <Parameters>
              <Parameter>
                <Name>DeveloperSupportEmail</Name>
                <Text/>
                <Value></Value>
                <ValueType>Text</ValueType>
              </Parameter>
              <Parameter>
                <Name>SupportEmailButton</Name>
                <Text>Write an e-mail to support</Text>
                <EventId>EMAIL_TO_SUPPORT</EventId>
                <Value>8631</Value>
                <ValueType>PictureResourceButton</ValueType>
                <WidthInRow>5</WidthInRow>
              </Parameter>
            </Parameters>
          </Parameter>
          <Parameter>
            <Name>DeveloperHomepageRow</Name>
            <Text>Homepage</Text>
            <ValueType>Row</ValueType>
            <Parameters>
              <Parameter>
                <Name>DeveloperHomepage</Name>
                <Text/>
                <Value></Value>
                <ValueType>Text</ValueType>
              </Parameter>
              <Parameter>
                <Name>HomepageButton</Name>
                <Text>Go to the homepage</Text>
                <EventId>GO_TO_HOMEPAGE</EventId>
                <Value>8631</Value>
                <ValueType>PictureResourceButton</ValueType>
                <WidthInRow>5</WidthInRow>
              </Parameter>
            </Parameters>
          </Parameter>
        </Parameters>
      </Parameter>
    </Parameters>
  </Page>

  <Page>
    <Name>__HiddenPage__</Name>
    <Text></Text>
    <Parameters>
      <Parameter>
        <Name>PluginStates</Name>
        <Text />
        <Value>[_]</Value>
        <ValueType>Integer</ValueType>
      </Parameter>
      <Parameter>
        <Name>PluginHasGitHubRepo</Name>
        <Text />
        <Value>[_]</Value>
        <ValueType>CheckBox</ValueType>
      </Parameter>
      <Parameter>
        <Name>CurrentPaletteState</Name>
        <Text />
        <Value>2001</Value>
        <ValueType>Integer</ValueType>
      </Parameter>
    </Parameters>
  </Page>
</Element>