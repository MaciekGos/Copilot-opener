' Copilot Opener - jedno klikniecie / one click.
' Uruchamia build.bat calkowicie w tle (bez okna terminala).
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
sh.Run "cmd /c build.bat", 0, False
