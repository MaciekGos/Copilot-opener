 <p align="center">
  <img src="logo.svg" alt="Copilot Opener" width="160">
</p>

<h1 align="center">Copilot Opener</h1>

<p align="center">
  A lightweight Windows utility that launches <strong>GitHub Copilot</strong> and your <strong>newest Android emulator</strong> with a single click.
</p>

<p align="center">
  <strong>Less setup. More vibe coding.</strong>
</p>

Originally created because I thought it would be useful to have both tools ready when vibe coding Android applications.

## Features

- <img src="https://api.iconify.design/ph/rocket-launch.svg?color=%23FFFFFF" width="18" height="18" /> **Quick launch** — start GitHub Copilot and your newest Android Virtual Device (AVD) automatically.
- <img src="https://api.iconify.design/ph/github-logo.svg?color=%23FFFFFF" width="18" height="18" /> **GitHub Copilot** — launches your AI coding companion.
- <img src="https://api.iconify.design/ph/android-logo.svg?color=%23FFFFFF" width="18" height="18" /> **Android Emulator** — automatically detects and launches the newest available AVD based on API level.
- <img src="https://api.iconify.design/ph/push-pin.svg?color=%23FFFFFF" width="18" height="18" /> **Always on top** — optionally keeps the emulator, its toolbar and extended controls above other windows.
- <img src="https://api.iconify.design/ph/tray.svg?color=%23FFFFFF" width="18" height="18" /> **System tray** — stays quietly in the background with quick access to all features.
- <img src="https://api.iconify.design/ph/translate.svg?color=%23FFFFFF" width="18" height="18" /> **Bilingual interface** — Polish and English, automatically detected with manual switching.
- <img src="https://api.iconify.design/ph/windows-logo.svg?color=%23FFFFFF" width="18" height="18" /> **Windows startup** — optionally launches automatically when Windows starts.
- <img src="https://api.iconify.design/ph/feather.svg?color=%23FFFFFF" width="18" height="18" /> **Lightweight** — simple utility without unnecessary complexity.

## System Tray

The tray menu provides quick access to:

- Launch everything
- Launch Copilot only
- Launch emulator only
- Toggle emulator always-on-top
- Enable or disable Windows startup
- Change application language
- Open configuration file
- Exit the application

Running the launcher again while it is already running triggers another launch instead of creating a second instance.

## Installation

1. Download `CopilotOpener_Setup.exe` from the latest GitHub Release.
2. Run the installer.
3. Choose your language and installation options.
4. Optionally enable a desktop shortcut or Windows startup.
5. Select **Launch Copilot Opener** on the final page.

The installer includes a full setup wizard with language selection, installation directory selection, progress tracking and an option to launch the application after installation.

It also works as an updater when an older version is already installed. The installer automatically closes the running application before updating or uninstalling.

> **Note:** The installer is not code-signed, so Windows SmartScreen may display a warning.

## Requirements

- Windows 10/11
- GitHub Copilot desktop app
- Android Studio
- Android SDK with at least one configured Android Virtual Device (AVD)

## Configuration

If Copilot or the Android SDK is not detected automatically, you can edit the configuration file:

`%APPDATA%\CopilotOpener\config.json`

You can access it directly from the system tray menu using **Open config file**.

Available configuration options include:

- `copilot_path` — path to the GitHub Copilot executable.
- `copilot_app_name` — Copilot application name.
- `sdk_path` — Android SDK directory.

## Developer Build

The repository also includes `Start.vbs`, providing a one-click, windowless build process with a progress window.

Inno Setup 6/7 is automatically detected or installed if needed.

## Disclaimer

A small personal utility project made for convenience.

Not affiliated with, endorsed by, or officially connected to GitHub, Microsoft, or Google.

## License

MIT License.
