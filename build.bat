@echo off
rem Copilot Opener - build worker. Uruchamiaj przez Start.vbs (bez okna terminala).
rem Run through Start.vbs (no terminal window).
setlocal
cd /d "%~dp0"
del /q build.log status.txt 2>nul

>status.txt echo START
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0progress.ps1"

where python >nul 2>nul
if errorlevel 1 ( call :fail ERR_PYTHON & exit /b 1 )

>status.txt echo DEPS
python -m pip install --quiet --upgrade pyinstaller pillow pystray >>build.log 2>&1
if errorlevel 1 ( call :fail ERR_PIP & exit /b 1 )

>status.txt echo ICON
python make_icon.py >>build.log 2>&1
if errorlevel 1 ( call :fail ERR_ICON & exit /b 1 )

>status.txt echo EXE
python -m PyInstaller --noconfirm --onefile --noconsole --name CopilotOpener --icon icon.ico --add-data "icon.ico;." --hidden-import pystray._win32 copilot_opener.pyw >>build.log 2>&1
if errorlevel 1 ( call :fail ERR_EXE & exit /b 1 )

>status.txt echo INNO
call :findiscc
if not defined ISCC (
    >status.txt echo INNO_DL
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://jrsoftware.org/download.php/is.exe' -OutFile '%TEMP%\innosetup.exe'" >>build.log 2>&1
    if errorlevel 1 ( call :fail ERR_INNO_DL & exit /b 1 )
    >status.txt echo INNO_INSTALL
    "%TEMP%\innosetup.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER >>build.log 2>&1
    call :findiscc
)
if not defined ISCC ( call :fail ERR_INNO_DL & exit /b 1 )

>status.txt echo SETUP
"%ISCC%" installer.iss >>build.log 2>&1
if errorlevel 1 ( call :fail ERR_SETUP & exit /b 1 )

>status.txt echo DONE
start "" "%~dp0installer_output\CopilotOpener_Setup.exe"
exit /b 0

:findiscc
set "ISCC="
for %%V in (6 7) do (
    if exist "%LocalAppData%\Programs\Inno Setup %%V\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup %%V\ISCC.exe"
    if exist "%ProgramFiles%\Inno Setup %%V\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup %%V\ISCC.exe"
    if exist "%ProgramFiles(x86)%\Inno Setup %%V\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup %%V\ISCC.exe"
)
exit /b 0

:fail
>status.txt echo %1
exit /b 0
