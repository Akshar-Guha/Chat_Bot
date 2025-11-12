@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ========================================
echo Starting EideticRAG Backend Server
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo.
    echo --- DIAGNOSTICS ---
    echo Python executable being used:
    where python
    echo -------------------
    echo.
) else (
    echo WARNING: Virtual environment not found. Using system Python.
)

REM Ensure Ollama daemon is running
if "%OLLAMA_HOST%"=="" set "OLLAMA_HOST=http://127.0.0.1:11434"
call :ensure_ollama

REM Validate backend port availability
set "BACKEND_HOST=127.0.0.1"
set "BACKEND_PORT=8000"
if not "%RAG_BACKEND_PORT%"=="" set "BACKEND_PORT=%RAG_BACKEND_PORT%"
if not "%RAG_BACKEND_HOST%"=="" set "BACKEND_HOST=%RAG_BACKEND_HOST%"
echo.
echo Checking availability of backend port %BACKEND_PORT%...
echo Automatically terminating any existing process on port %BACKEND_PORT%…
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%BACKEND_PORT% ^| findstr LISTENING') do (
    taskkill /F /PID %%a
)

echo.
echo Starting backend on http://%BACKEND_HOST%:%BACKEND_PORT%...
echo Press Ctrl+C to stop the server
echo.

.\.venv\Scripts\python.exe -m uvicorn eidetic_rag.backend.app.main:app --host %BACKEND_HOST% --port %BACKEND_PORT% --reload
set "PY_EXIT=%ERRORLEVEL%"

if "%PY_EXIT%"=="0" goto :backend_success
if "%PY_EXIT%"=="-1073741510" goto :backend_cancelled
if "%PY_EXIT%"=="3221225786" goto :backend_cancelled

echo [ERROR] Backend exited with code %PY_EXIT%.
goto :pause_fail

:backend_cancelled
echo Backend stopped by user.
goto :pause_success

:backend_success
echo Backend exited normally.
goto :pause_success

:pause_fail
echo.
pause
endlocal
exit /b %PY_EXIT%

:pause_success
echo.
pause
endlocal
exit /b 0

:port_conflict_abort
echo.
echo Startup aborted because port %BACKEND_PORT% is still in use.
echo.
pause
endlocal
exit /b 1

:ensure_ollama
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama CLI not found in PATH. Please install Ollama from https://ollama.ai/
    exit /b 0
)

echo Checking Ollama daemon at %OLLAMA_HOST%...
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri '%OLLAMA_HOST%/api/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% neq 0 (
    echo Ollama daemon not detected. Starting it now...
    start "" /B ollama serve
    echo Waiting for Ollama to initialize...
    powershell -NoProfile -Command "for($i=0;$i -lt 10;$i++){ try { Invoke-RestMethod -Uri '%OLLAMA_HOST%/api/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 500 } } exit 1"
    if %errorlevel% neq 0 (
        echo WARNING: Unable to confirm Ollama startup. Continuing backend launch.
    ) else (
        echo Ollama daemon is ready.
    )
) else (
    echo Ollama daemon already running.
)
exit /b 0

:ensure_port_free
if not "%~1"=="" set "PORT_TO_CHECK=%~1"

:check_port_loop
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

echo Terminated process %PORT_PID%. Rechecking port...
goto :check_port_loop
