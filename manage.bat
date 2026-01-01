@echo off
REM CheckIn App V2 - Unified Process Manager (Windows)
REM Usage: manage.bat {start|stop|restart|status|log} [backend|frontend|all]

chcp 65001 >nul 2>&1

setlocal EnableDelayedExpansion

cd /d "%~dp0"

set APP_DIR=%~dp0
set VENV_DIR=%APP_DIR%venv
set BACKEND_PID_FILE=%APP_DIR%backend.pid
set FRONTEND_PID_FILE=%APP_DIR%frontend.pid
set BACKEND_LOG_FILE=%APP_DIR%logs\backend.log
set FRONTEND_LOG_FILE=%APP_DIR%logs\frontend.log
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

REM Parse command and target
set COMMAND=%1
set TARGET=%2

REM Default target is 'all' if not specified
if "%TARGET%"=="" set TARGET=all

if "%COMMAND%"=="" goto usage
if "%COMMAND%"=="start" goto start
if "%COMMAND%"=="stop" goto stop
if "%COMMAND%"=="restart" goto restart
if "%COMMAND%"=="status" goto status
if "%COMMAND%"=="log" goto log
if "%COMMAND%"=="build" goto build
goto usage

REM ============================================
REM START COMMAND
REM ============================================
:start
if "%TARGET%"=="backend" goto start_backend
if "%TARGET%"=="frontend" goto start_frontend
if "%TARGET%"=="all" goto start_all
echo [ERROR] Invalid target: %TARGET%
goto usage

:start_all
echo ========================================
echo CheckIn App V2 - Starting All Services
echo ========================================
echo.
call :start_backend_internal
echo.
call :start_frontend_internal
echo.
echo ========================================
echo All Services Started!
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend App: http://localhost:3000
echo.
goto end

:start_backend
echo ========================================
echo CheckIn App V2 - Starting Backend
echo ========================================
echo.
call :start_backend_internal
goto end

:start_frontend
echo ========================================
echo CheckIn App V2 - Starting Frontend
echo ========================================
echo.
call :start_frontend_internal
goto end

REM --- Backend Start Logic ---
:start_backend_internal
REM Check if already running
if exist "%BACKEND_PID_FILE%" (
    set /p PID=<"%BACKEND_PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "python.exe">NUL
    if "!ERRORLEVEL!"=="0" (
        echo [WARNING] Backend is already running (PID: !PID!)
        exit /b 0
    ) else (
        REM Silently clean up stale PID file (don't show message)
        del "%BACKEND_PID_FILE%" >nul 2>&1
    )
)

REM Check virtual environment
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment does not exist: %VENV_DIR%
    echo [INFO] Please run first: python -m venv venv
    exit /b 1
)

REM Check required directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "sessions" mkdir sessions

echo [INFO] Starting backend service in background...

REM Create a VBS script to run Python invisibly (using venv's python.exe directly)
set VBS_FILE=%TEMP%\start_backend.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_FILE%"
echo WshShell.Run """%PYTHON_EXE%"" ""%APP_DIR%run_daemon.py""", 0, False >> "%VBS_FILE%"
cscript //nologo "%VBS_FILE%"
del "%VBS_FILE%" >nul 2>&1

echo [INFO] Waiting for backend to start...
timeout /t 3 /nobreak >nul

REM Check if port 8000 is listening
set SERVICE_RUNNING=0
for /L %%i in (1,1,10) do (
    netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        set SERVICE_RUNNING=1
        goto :backend_port_found
    )
    timeout /t 1 /nobreak >nul
)

:backend_port_found
if "%SERVICE_RUNNING%"=="1" (
    REM Find the PID of the process listening on port 8000
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        set LAST_PID=%%a
        goto :backend_pid_found
    )

    :backend_pid_found
    if defined LAST_PID (
        echo !LAST_PID! > "%BACKEND_PID_FILE%"
        echo [OK] Backend started successfully (PID: !LAST_PID!)
        echo      API Docs: http://localhost:8000/docs
        echo      Log: %BACKEND_LOG_FILE%
        exit /b 0
    )
) else (
    echo [ERROR] Backend failed to start - port 8000 not listening
    echo [INFO] Check log: %BACKEND_LOG_FILE%
    echo.
    echo [DEBUG] Last 10 lines of log:
    if exist "%BACKEND_LOG_FILE%" (
        powershell -Command "$OutputEncoding = [System.Text.Encoding]::UTF8; Get-Content '%BACKEND_LOG_FILE%' -Encoding UTF8 -Tail 10"
    ) else (
        echo Log file not found
    )
    exit /b 1
)
exit /b 0

REM --- Frontend Start Logic ---
:start_frontend_internal
REM Check if already running
if exist "%FRONTEND_PID_FILE%" (
    set /p PID=<"%FRONTEND_PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "node.exe">NUL
    if "!ERRORLEVEL!"=="0" (
        echo [WARNING] Frontend is already running (PID: !PID!)
        exit /b 0
    ) else (
        REM Silently clean up stale PID file (don't show message)
        del "%FRONTEND_PID_FILE%" >nul 2>&1
    )
)

REM Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found
    echo [INFO] Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Check frontend directory
if not exist "frontend" (
    echo [ERROR] Frontend directory not found
    exit /b 1
)

REM Check node_modules
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo [INFO] Starting frontend service in background...

REM Create VBS script to run npm dev invisibly
set VBS_FILE=%TEMP%\start_frontend.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_FILE%"
echo WshShell.CurrentDirectory = "%APP_DIR%frontend" >> "%VBS_FILE%"
echo Set fso = CreateObject("Scripting.FileSystemObject") >> "%VBS_FILE%"
echo Set logFile = fso.CreateTextFile("%FRONTEND_LOG_FILE%", True) >> "%VBS_FILE%"
echo logFile.WriteLine "Frontend service starting at " ^& Now >> "%VBS_FILE%"
echo logFile.Close >> "%VBS_FILE%"
echo WshShell.Run "cmd /c npm run dev >> ""%FRONTEND_LOG_FILE%"" 2>&1", 0, False >> "%VBS_FILE%"
cscript //nologo "%VBS_FILE%"
del "%VBS_FILE%" >nul 2>&1

echo [INFO] Waiting for frontend to start...
timeout /t 3 /nobreak >nul

REM Check if port 5000 is listening (Vite configured port)
set SERVICE_RUNNING=0
for /L %%i in (1,1,10) do (
    netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        set SERVICE_RUNNING=1
        goto :frontend_port_found
    )
    timeout /t 1 /nobreak >nul
)

:frontend_port_found
if "%SERVICE_RUNNING%"=="1" (
    REM Find the PID of the process listening on port 3000
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
        set LAST_PID=%%a
        goto :frontend_pid_found
    )

    :frontend_pid_found
    if defined LAST_PID (
        echo !LAST_PID! > "%FRONTEND_PID_FILE%"
        echo [OK] Frontend started successfully (PID: !LAST_PID!)
        echo      URL: http://localhost:3000
        echo      Log: %FRONTEND_LOG_FILE%
        exit /b 0
    )
) else (
    echo [ERROR] Frontend failed to start - port 3000 not listening
    echo [INFO] Check log: %FRONTEND_LOG_FILE%
    echo.
    echo [DEBUG] Last 10 lines of log:
    if exist "%FRONTEND_LOG_FILE%" (
        powershell -Command "$OutputEncoding = [System.Text.Encoding]::UTF8; Get-Content '%FRONTEND_LOG_FILE%' -Encoding UTF8 -Tail 10"
    ) else (
        echo Log file not found
    )
    exit /b 1
)
exit /b 0

REM ============================================
REM STOP COMMAND
REM ============================================
:stop
if "%TARGET%"=="backend" goto stop_backend
if "%TARGET%"=="frontend" goto stop_frontend
if "%TARGET%"=="all" goto stop_all
echo [ERROR] Invalid target: %TARGET%
goto usage

:stop_all
echo ========================================
echo CheckIn App V2 - Stopping All Services
echo ========================================
echo.
call :stop_backend_internal
echo.
call :stop_frontend_internal
goto end

:stop_backend
call :stop_backend_internal
goto end

:stop_frontend
call :stop_frontend_internal
goto end

REM --- Backend Stop Logic ---
:stop_backend_internal
echo [INFO] Stopping backend...

REM First try to kill by port
set BACKEND_KILLED=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        echo [OK] Backend stopped ^(PID: %%a^)
        set BACKEND_KILLED=1
        REM Delete PID file immediately after successful kill
        if exist "%BACKEND_PID_FILE%" (
            del "%BACKEND_PID_FILE%" >nul 2>&1
        )
    )
)

REM Then try PID file if port method didn't work
if "%BACKEND_KILLED%"=="0" (
    if exist "%BACKEND_PID_FILE%" (
        set /p PID=<"%BACKEND_PID_FILE%"
        tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "python.exe">NUL
        if "!ERRORLEVEL!"=="0" (
            taskkill /F /T /PID !PID! >nul 2>&1
            if "!ERRORLEVEL!"=="0" (
                echo [OK] Backend stopped ^(PID: !PID!^)
                set BACKEND_KILLED=1
                REM Delete PID file immediately after successful kill
                del "%BACKEND_PID_FILE%" >nul 2>&1
            )
        ) else (
            REM Process doesn't exist, just clean up the stale PID file
            del "%BACKEND_PID_FILE%" >nul 2>&1
        )
    )

    REM Only show warning if nothing was stopped
    if "%BACKEND_KILLED%"=="0" (
        echo [WARNING] Backend not running
    )
)

exit /b 0

REM --- Frontend Stop Logic ---
:stop_frontend_internal
echo [INFO] Stopping frontend...

REM First try to kill by port
set FRONTEND_KILLED=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /T /PID %%a >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        echo [OK] Frontend stopped ^(PID: %%a^)
        set FRONTEND_KILLED=1
        REM Delete PID file immediately after successful kill
        if exist "%FRONTEND_PID_FILE%" (
            del "%FRONTEND_PID_FILE%" >nul 2>&1
        )
    )
)

REM Also check ports 5001-5010 (Vite fallback ports)
if "%FRONTEND_KILLED%"=="0" (
    for /L %%p in (3001,1,3010) do (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p" ^| findstr "LISTENING"') do (
            REM Check if it's a node process
            tasklist /FI "PID eq %%a" 2>NUL | find /I /N "node.exe">NUL
            if "!ERRORLEVEL!"=="0" (
                taskkill /F /T /PID %%a >nul 2>&1
                if "!ERRORLEVEL!"=="0" (
                    echo [OK] Frontend stopped ^(PID: %%a, Port: %%p^)
                    set FRONTEND_KILLED=1
                    REM Delete PID file immediately after successful kill
                    if exist "%FRONTEND_PID_FILE%" (
                        del "%FRONTEND_PID_FILE%" >nul 2>&1
                    )
                )
            )
        )
    )
)

REM Then try PID file if port method didn't work
if "%FRONTEND_KILLED%"=="0" (
    if exist "%FRONTEND_PID_FILE%" (
        set /p PID=<"%FRONTEND_PID_FILE%"
        tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "node.exe">NUL
        if "!ERRORLEVEL!"=="0" (
            taskkill /F /T /PID !PID! >nul 2>&1
            if "!ERRORLEVEL!"=="0" (
                echo [OK] Frontend stopped ^(PID: !PID!^)
                set FRONTEND_KILLED=1
                REM Delete PID file immediately after successful kill
                del "%FRONTEND_PID_FILE%" >nul 2>&1
            )
        ) else (
            REM Process doesn't exist, just clean up the stale PID file
            del "%FRONTEND_PID_FILE%" >nul 2>&1
        )
    )

    REM Only show warning if nothing was stopped
    if "%FRONTEND_KILLED%"=="0" (
        echo [WARNING] Frontend not running
    )
)

exit /b 0

REM ============================================
REM RESTART COMMAND
REM ============================================
:restart
echo [INFO] Restarting %TARGET%...
echo.
call :stop
timeout /t 2 /nobreak >nul

REM Force cleanup of any remaining PID files before starting
if "%TARGET%"=="backend" (
    del "%BACKEND_PID_FILE%" >nul 2>&1
)
if "%TARGET%"=="frontend" (
    del "%FRONTEND_PID_FILE%" >nul 2>&1
)
if "%TARGET%"=="all" (
    del "%BACKEND_PID_FILE%" >nul 2>&1
    del "%FRONTEND_PID_FILE%" >nul 2>&1
)

call :start
goto end

REM ============================================
REM STATUS COMMAND
REM ============================================
:status
echo ========================================
echo CheckIn App V2 - Service Status
echo ========================================
echo.

if "%TARGET%"=="backend" goto status_backend
if "%TARGET%"=="frontend" goto status_frontend
if "%TARGET%"=="all" goto status_all
echo [ERROR] Invalid target: %TARGET%
goto usage

:status_all
call :status_backend_internal
echo.
call :status_frontend_internal
goto end

:status_backend
call :status_backend_internal
goto end

:status_frontend
call :status_frontend_internal
goto end

REM --- Backend Status ---
:status_backend_internal
echo [Backend Service]

if not exist "%BACKEND_PID_FILE%" (
    echo   Status: NOT RUNNING
    exit /b 0
)

set /p PID=<"%BACKEND_PID_FILE%"
tasklist /FI "PID eq %PID%" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo   Status: RUNNING
    echo   PID: %PID%
    echo   URL: http://localhost:8000/docs
    echo   Log: %BACKEND_LOG_FILE%
    netstat -ano | findstr :8000 | findstr LISTENING
) else (
    echo   Status: NOT RUNNING
    del "%BACKEND_PID_FILE%" >nul 2>&1
)
exit /b 0

REM --- Frontend Status ---
:status_frontend_internal
echo [Frontend Service]

if not exist "%FRONTEND_PID_FILE%" (
    echo   Status: NOT RUNNING
    exit /b 0
)

set /p PID=<"%FRONTEND_PID_FILE%"
tasklist /FI "PID eq %PID%" 2>NUL | find /I /N "node.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo   Status: RUNNING
    echo   PID: %PID%
    echo   URL: http://localhost:3000
    echo   Log: %FRONTEND_LOG_FILE%
    netstat -ano | findstr :3000 | findstr LISTENING
) else (
    echo   Status: NOT RUNNING
    del "%FRONTEND_PID_FILE%" >nul 2>&1
)
exit /b 0

REM ============================================
REM LOG COMMAND
REM ============================================
:log
if "%TARGET%"=="backend" goto log_backend
if "%TARGET%"=="frontend" goto log_frontend
if "%TARGET%"=="all" (
    echo [ERROR] Cannot tail multiple logs simultaneously
    echo [INFO] Use: manage.bat log backend OR manage.bat log frontend
    goto usage
)
echo [ERROR] Invalid target: %TARGET%
goto usage

:log_backend
echo ========================================
echo Backend Real-time Logs (Press Ctrl+C to exit)
echo ========================================
echo.

if not exist "%BACKEND_LOG_FILE%" (
    echo [ERROR] Log file does not exist: %BACKEND_LOG_FILE%
    exit /b 1
)

powershell -Command "$OutputEncoding = [System.Text.Encoding]::UTF8; Get-Content '%BACKEND_LOG_FILE%' -Encoding UTF8 -Wait -Tail 20"
goto end

:log_frontend
echo ========================================
echo Frontend Real-time Logs (Press Ctrl+C to exit)
echo ========================================
echo.

if not exist "%FRONTEND_LOG_FILE%" (
    echo [ERROR] Log file does not exist: %FRONTEND_LOG_FILE%
    exit /b 1
)

powershell -Command "$OutputEncoding = [System.Text.Encoding]::UTF8; Get-Content '%FRONTEND_LOG_FILE%' -Encoding UTF8 -Wait -Tail 20"
goto end

REM ============================================
REM BUILD COMMAND
REM ============================================
:build
echo ========================================
echo CheckIn App V2 - Building Frontend
echo ========================================
echo.

REM Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found
    echo [INFO] Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Check frontend directory
if not exist "frontend" (
    echo [ERROR] Frontend directory not found
    exit /b 1
)

REM Check node_modules
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies first...
    cd frontend
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies
        exit /b 1
    )
    cd ..
    echo.
)

echo [INFO] Building frontend for production...
echo.

REM Build frontend
cd frontend
call npm run build
set BUILD_EXIT_CODE=%ERRORLEVEL%
cd ..

if %BUILD_EXIT_CODE% EQU 0 (
    echo.
    echo [OK] Frontend built successfully!

    REM Check if dist directory exists
    if exist "frontend\dist" (
        echo.
        echo Build output:
        echo   Location: %APP_DIR%frontend\dist

        REM Calculate directory size
        for /f "tokens=3" %%a in ('dir /s "frontend\dist" ^| find "bytes"') do set DIST_SIZE=%%a
        echo   Files: !DIST_SIZE! bytes

        echo.
        echo File structure:
        dir /B frontend\dist
        echo.
        echo [INFO] You can now deploy the 'frontend\dist' directory to your web server
    ) else (
        echo [WARNING] Build succeeded but dist directory not found
    )
) else (
    echo.
    echo [ERROR] Frontend build failed
    echo [INFO] Check the output above for error details
    exit /b 1
)
goto end

REM ============================================
REM USAGE
REM ============================================
:usage
echo CheckIn App V2 - Unified Process Manager
echo.
echo Usage: %~nx0 COMMAND [TARGET]
echo.
echo Commands:
echo   start [TARGET]   - Start service(s)
echo   stop [TARGET]    - Stop service(s)
echo   restart [TARGET] - Restart service(s)
echo   status [TARGET]  - View service(s) status
echo   log TARGET       - View real-time logs (backend or frontend only)
echo   build            - Build frontend for production
echo.
echo Targets:
echo   backend  - Backend API service (default port: 8000)
echo   frontend - Frontend dev server (default port: 5000)
echo   all      - Both services (default)
echo.
echo Examples:
echo   %~nx0 start              # Start both services
echo   %~nx0 start backend      # Start backend only
echo   %~nx0 stop all           # Stop all services
echo   %~nx0 status             # View all services status
echo   %~nx0 log backend        # View backend logs
echo   %~nx0 build              # Build frontend static files
echo   %~nx0 restart frontend   # Restart frontend
exit /b 1

:end
exit /b 0
