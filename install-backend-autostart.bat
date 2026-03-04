@echo off
setlocal
title TEI-HA Backend Auto-Start Installer

rem Determine project root
cd /d "%~dp0"

set "TASK_NAME=TEI-HA Backend"
set "SCRIPT_PATH=%~dp0start-backend-silent.bat"

if /I "%~1"=="remove" (
  echo Removing scheduled task "%TASK_NAME%"...
  schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
  if errorlevel 1 (
    echo Failed to remove or task not found.
  ) else (
    echo Removed.
  )
  goto :eof
)

if /I "%~1"=="status" (
  echo Querying status of "%TASK_NAME%"...
  schtasks /Query /TN "%TASK_NAME%" | findstr /I "%TASK_NAME%"
  goto :eof
)

if not exist "%SCRIPT_PATH%" (
  echo ERROR: start-backend-silent.bat not found at:
  echo   "%SCRIPT_PATH%"
  exit /b 1
)

echo Installing Windows Scheduled Task to auto-start backend at user logon...

rem Create task (runs minimized via the silent starter)
rem Quote the task action path correctly for spaces
set "TASK_ACTION=""%SCRIPT_PATH%"""

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR %TASK_ACTION% ^
  /SC ONLOGON ^
  /RL HIGHEST ^
  /F ^
  /RU "%USERNAME%" >nul

if errorlevel 1 (
  echo ERROR: Failed to create scheduled task.
  echo Try running this installer as Administrator.
  exit /b 1
)

echo Success!
echo - Task Name: %TASK_NAME%
echo - Action: "%SCRIPT_PATH%"
echo - Trigger: At logon for user %USERNAME%
echo.
echo You can verify with:
echo   install-backend-autostart.bat status
echo.
echo To remove later:
echo   install-backend-autostart.bat remove

endlocal
exit /b 0


