<?xml version="1.0" encoding="utf-8"?>
<Element>
    <Script>
        <Name>PluginHub.py</Name>
        <Title>ALLPLAN Plugin Hub</Title>
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
            <Name>GET_MORE_INFO</Name>
            <Value>1004</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <Constant>
            <Name>UNINSTALL</Name>
            <Value>1005</Value>
            <ValueType>Integer</ValueType>
        </Constant>
        <!-- Plugin states -->
    </Constants>
    <Page>


        <Parameter>
            <Name>PluginListGroup</Name>
            <ValueType>ListGroup</ValueType>
            <Parameter>
                <Name>TitleRow</Name>
                <Text>Foo</Text>
                <ValueType>Row</ValueType>
                <Value>OVERALL</Value>
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
                    <Name>MoreInfoButton</Name>
                    <Text>Go to the plugin home page</Text>
                    <EventId>GET_MORE_INFO</EventId>
                    <Value>AllplanSettings.PictResPalette.eHotinfo</Value>
                    <ValueType>PictureResourceButton</ValueType>
                    <Visible>PluginHasGitHubRepo[$list_row]</Visible>
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
            </Parameter>

            <Parameter>
                <Name>DescriptionRow</Name>
                <Text>Bar</Text>
                <ValueType>Row</ValueType>
                <Value>OVERALL</Value>
                <Parameter>
                    <Name>PluginDescriptions</Name>
                    <Text/>
                    <Value>[_]</Value>
                    <ValueType>Text</ValueType>
                    <Visible>PluginDescriptions[$list_row] != ""</Visible>
                    <FontStyle>1</FontStyle>
                </Parameter>
            </Parameter>
            <Parameter>
                <Name>Separator</Name>
                <ValueType>Separator</ValueType>
            </Parameter>
        </Parameter>

    </Page>
    <Page>
        <Name>__HiddenPage__</Name>
        <Text></Text>
        <Parameter>
            <Name>PluginStates</Name>
            <Text/>
            <Value>[_]</Value>
            <ValueType>Integer</ValueType>
        </Parameter>
        <Parameter>
            <Name>PluginHasGitHubRepo</Name>
            <Text/>
            <Value>[_]</Value>
            <ValueType>Checkbox</ValueType>
        </Parameter>
    </Page>
</Element>
