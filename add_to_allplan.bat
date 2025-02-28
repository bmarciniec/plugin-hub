@echo off
REM This script will place symbolic link in your ALLLPLAN Usr or Std directory pointing to this repository
REM for testing purposes
set /p action="Do you want to install (i) or remove (R) the links? "
set /p targetPath="Please enter the Path to Usr or Std (with trailing \): "


if exist "%targetPath%Library\Plugin Hub.pyp" (
    del "%targetPath%Library\Plugin Hub.pyp"
    echo "Removed %targetPath%Library\Plugin Hub.pyp"
) else (
    echo "Link %targetPath%Library\Plugin Hub.pyp does not exist"
)

if exist "%targetPath%PythonPartsScripts\PluginHub" (
    rmdir /S /Q "%targetPath%PythonPartsScripts\PluginHub"
    echo "Removed %targetPath%PythonPartsScripts\PluginHub"
) else (
    echo "Link %targetPath%PythonPartsScripts\PluginHub does not exist"
)

echo "Removal process completed"


if /I "%action%"=="i" (
    goto :install
) else if /I "%action%"=="R" (
    echo "Press any key to continue."
    pause >null
    exit /b 0
)

:install

set scriptDir=%~dp0

if not exist "%targetPath%\PythonPartsScripts" (
    mkdir "%targetPath%\PythonPartsScripts"
)

mklink "%targetPath%Library\Plugin Hub.pyp" "%scriptDir%Library\Plugin Hub.pyp"
mklink /D "%targetPath%PythonPartsScripts\PluginHub" "%scriptDir%PythonPartsScripts\PluginHub"

echo "PythonPart installed in Allplan. You'll find it in Library -> Office or Private -> Plugin Hub."
echo "Press any key to continue"
pause >nul
exit /b 0

