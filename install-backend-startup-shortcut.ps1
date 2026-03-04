Param(
  [switch]$Remove
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupDir = [Environment]::GetFolderPath('Startup')
$lnkPath = Join-Path $startupDir 'TEI-HA Backend (Auto-Start).lnk'
$targetBat = Join-Path $projectRoot 'start-backend-silent.bat'

if ($Remove) {
  if (Test-Path $lnkPath) {
    Remove-Item -Force $lnkPath
    Write-Host "Removed startup shortcut: $lnkPath"
  } else {
    Write-Host "No startup shortcut found to remove."
  }
  exit 0
}

if (!(Test-Path $targetBat)) {
  Write-Host "ERROR: start-backend-silent.bat not found at:" -ForegroundColor Red
  Write-Host "  $targetBat" -ForegroundColor Yellow
  exit 1
}

Write-Host "Creating startup shortcut to auto-start backend on login..." -ForegroundColor Cyan

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($lnkPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $projectRoot
$shortcut.WindowStyle = 7    # Minimized
$shortcut.Description = "Starts TEI-HA backend silently at login"
$shortcut.Save()

Write-Host "Success!" -ForegroundColor Green
Write-Host "Shortcut: $lnkPath" -ForegroundColor Gray
Write-Host "It will run: $targetBat" -ForegroundColor Gray


