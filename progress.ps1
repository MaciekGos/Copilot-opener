Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$pl = (Get-UICulture).TwoLetterISOLanguageName -eq 'pl'
$i = if ($pl) { 0 } else { 1 }
$status = Join-Path $PSScriptRoot 'status.txt'
$log = Join-Path $PSScriptRoot 'build.log'

$T = @{
  START       = @('Przygotowuję instalator...', 'Preparing the installer...')
  DEPS        = @('Instaluję potrzebne biblioteki...', 'Installing required libraries...')
  ICON        = @('Tworzę ikonę...', 'Creating the icon...')
  EXE         = @('Buduję program (to potrwa chwilę)...', 'Building the app (this takes a moment)...')
  INNO        = @('Szukam Inno Setup...', 'Looking for Inno Setup...')
  INNO_DL     = @('Pobieram Inno Setup...', 'Downloading Inno Setup...')
  INNO_INSTALL= @('Instaluję Inno Setup...', 'Installing Inno Setup...')
  SETUP       = @('Buduję instalator...', 'Building the installer...')
  DONE        = @('Gotowe!', 'Done!')
  ERR_PYTHON  = @('Nie znaleziono Pythona. Zainstaluj go z python.org (zaznacz "Add python.exe to PATH") i uruchom Start.vbs ponownie.',
                  'Python was not found. Install it from python.org (tick "Add python.exe to PATH") and run Start.vbs again.')
  ERR_PIP     = @('Nie udało się zainstalować bibliotek (sprawdź internet).', 'Could not install the libraries (check your internet connection).')
  ERR_ICON    = @('Nie udało się utworzyć ikony.', 'Could not create the icon.')
  ERR_EXE     = @('Nie udało się zbudować programu.', 'Could not build the app.')
  ERR_INNO_DL = @('Nie udało się pobrać/zainstalować Inno Setup. Zainstaluj go ręcznie z jrsoftware.org i uruchom Start.vbs ponownie.',
                  'Could not download/install Inno Setup. Install it manually from jrsoftware.org and run Start.vbs again.')
  ERR_SETUP   = @('Nie udało się zbudować instalatora.', 'Could not build the installer.')
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Copilot Opener'
$form.Size = New-Object System.Drawing.Size(440, 150)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true
$iconPath = Join-Path $PSScriptRoot 'icon.ico'
if (Test-Path $iconPath) { try { $form.Icon = New-Object System.Drawing.Icon($iconPath) } catch {} }

$label = New-Object System.Windows.Forms.Label
$label.Text = $T['START'][$i]
$label.Location = New-Object System.Drawing.Point(20, 20)
$label.Size = New-Object System.Drawing.Size(390, 40)
$label.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$form.Controls.Add($label)

$bar = New-Object System.Windows.Forms.ProgressBar
$bar.Style = 'Marquee'
$bar.MarqueeAnimationSpeed = 30
$bar.Location = New-Object System.Drawing.Point(20, 70)
$bar.Size = New-Object System.Drawing.Size(390, 22)
$form.Controls.Add($bar)

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 400
$timer.Add_Tick({
  try { $s = (Get-Content -Raw -Path $status -ErrorAction Stop).Trim() } catch { return }
  if (-not $T.ContainsKey($s)) { return }
  $label.Text = $T[$s][$i]
  if ($s -eq 'DONE') {
    $timer.Stop(); $form.Close()
  } elseif ($s -like 'ERR_*') {
    $timer.Stop(); $bar.Style = 'Continuous'; $bar.Value = 0
    $form.TopMost = $false
    $extra = if ($pl) { "`n`nSzczegóły: $log" } else { "`n`nDetails: $log" }
    [System.Windows.Forms.MessageBox]::Show($T[$s][$i] + $extra, 'Copilot Opener', 'OK', 'Error') | Out-Null
    $form.Close()
  }
})
$timer.Start()
[void]$form.ShowDialog()
