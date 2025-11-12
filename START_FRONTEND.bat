@echo off
setlocal

echo ========================================
echo Starting EideticRAG Frontend
echo ========================================
echo.

set "FRONTEND_DIR=%~dp0src\frontend"
set "FRONTEND_HOST=localhost"
set "FRONTEND_PORT=3000"
if not "%RAG_FRONTEND_PORT%"=="" set "FRONTEND_PORT=%RAG_FRONTEND_PORT%"
if not "%RAG_FRONTEND_HOST%"=="" set "FRONTEND_HOST=%RAG_FRONTEND_HOST%"

pushd "%FRONTEND_DIR%" >nul 2>&1 || goto :missing_dir

if not exist node_modules goto :install
echo Dependencies already installed. Skipping npm install.
goto :after_install

:install
echo Installing dependencies (first run detected)...
call npm install
if errorlevel 1 goto :install_fail

:after_install

echo Checking availability of frontend port %FRONTEND_PORT%...
call :ensure_port_free %FRONTEND_PORT%
if errorlevel 1 goto :start_fail

echo.
echo Starting frontend on http://%FRONTEND_HOST%:%FRONTEND_PORT%...
echo Press Ctrl+C to stop the server
echo.

set "HOST=%FRONTEND_HOST%"
set "PORT=%FRONTEND_PORT%"

call npm start
set "START_EXIT=%ERRORLEVEL%"

popd >nul

if "%START_EXIT%"=="0" goto :end
if "%START_EXIT%"=="-1073741510" goto :user_cancelled
if "%START_EXIT%"=="3221225786" goto :user_cancelled
goto :start_fail
goto :end

:missing_dir
echo [ERROR] Could not locate frontend directory at "%FRONTEND_DIR%".
goto :pause_fail

:install_fail
echo [ERROR] npm install failed. See output above for details.
popd >nul
goto :pause_fail

:start_fail
echo [ERROR] npm start exited with code %START_EXIT%.

:pause_fail
echo.
pause
endlocal
exit /b 1

:user_cancelled
echo Frontend stopped by user.
goto :end

:end
echo Frontend started successfully.
echo.
pause
endlocal
exit /b 0

:ensure_port_free
if "%~1"=="" exit /b 0
set "PORT_TO_CHECK=%~1"

set "PORT_PID="
for /f "usebackq tokens=*" %%p in (`powershell -NoProfile -Command "try { Get-NetTCPConnection -State Listen -LocalPort %PORT_TO_CHECK% -ErrorAction Stop | Select-Object -ExpandProperty OwningProcess -Unique } catch { '' }"`) do set "PORT_PID=%%p"

if "%PORT_PID%"=="" exit /b 0

set "PORT_PROCESS_NAME="
for /f "usebackq tokens=*" %%n in (`powershell -NoProfile -Command "try { (Get-Process -Id %PORT_PID%).ProcessName } catch { '' }"`) do set "PORT_PROCESS_NAME=%%n"
if "%PORT_PROCESS_NAME%"=="" set "PORT_PROCESS_NAME=unknown process"

echo WARNING: Port %PORT_TO_CHECK% is already in use by PID %PORT_PID% (%PORT_PROCESS_NAME%).
choice /C YN /M "Terminate this process now?"
if errorlevel 2 (
    echo Please stop the conflicting process and rerun this script.
    exit /b 1
)

powershell -NoProfile -Command "try { Stop-Process -Id %PORT_PID% -Force -ErrorAction Stop; exit 0 } catch { exit 1 }"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to terminate process %PORT_PID%.
    exit /b 1
)

echo Terminated process %PORT_PID%. Continuing startup...
exit /b 0
