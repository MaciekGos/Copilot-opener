; Instalator / Installer - Copilot Opener (Inno Setup 6/7)
#define MyAppName "Copilot Opener"
#define MyAppVersion "2.2"
#define MyAppExe "CopilotOpener.exe"
#define HavePolish FileExists(CompilerPath + "Languages\Polish.isl")

[Setup]
AppId={{B7C1F3A2-5D4E-4F6A-9C21-0A1B2C3D4E5F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableDirPage=no
DisableReadyPage=no
ShowLanguageDialog=yes
UsePreviousLanguage=no
UsePreviousTasks=no
OutputDir=installer_output
OutputBaseFilename=CopilotOpener_Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExe}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
#if HavePolish
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
#endif
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
#if HavePolish
polish.TaskDesktop=Utwórz skrót na pulpicie
polish.TaskAutostart=Uruchamiaj z Windows (tylko w zasobniku, bez odpalania aplikacji)
polish.GroupShortcuts=Skróty:
polish.GroupExtra=Dodatkowo:
polish.RunApp=Uruchom {#MyAppName} (odpali Copilota i emulator)
#endif
english.TaskDesktop=Create a desktop shortcut
english.TaskAutostart=Start with Windows (tray only, without launching the apps)
english.GroupShortcuts=Shortcuts:
english.GroupExtra=Additional:
english.RunApp=Launch {#MyAppName} (starts Copilot and the emulator)

[Tasks]
Name: "desktopicon"; Description: "{cm:TaskDesktop}"; GroupDescription: "{cm:GroupShortcuts}"
Name: "autostart"; Description: "{cm:TaskAutostart}"; GroupDescription: "{cm:GroupExtra}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.svg"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "CopilotOpener"; ValueData: """{app}\{#MyAppExe}"" --no-launch"; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:RunApp}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#MyAppExe}"; Flags: runhidden; RunOnceId: "KillCopilotOpener"

[Code]
// Zamknij dzialajaca aplikacje (siedzi w zasobniku) przed podmiana pliku.
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  rc: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#MyAppExe}', '', SW_HIDE, ewWaitUntilTerminated, rc);
  Result := '';
end;
