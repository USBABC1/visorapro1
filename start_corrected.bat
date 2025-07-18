@echo off
title Video Editor Pro
echo ========================================
echo    Video Editor Pro - Starting Application
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

:: Check if backend directory exists
if not exist "backend" (
    echo ERROR: Backend directory not found
    echo Please ensure you're in the project root directory
    pause
    exit /b 1
)

:: Activate virtual environment
echo [1/6] Activating virtual environment...
call venv\Scripts\activate.bat

:: Check critical dependencies
echo [2/6] Checking dependencies...
python -c "import torch, transformers, fastapi" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python dependencies not installed correctly
    echo Please run setup.bat again
    pause
    exit /b 1
)

:: Check MoviePy specifically
python -c "from moviepy.editor import VideoFileClip" >nul 2>&1
if errorlevel 1 (
    echo WARNING: MoviePy issue detected, reinstalling...
    python -m pip install --force-reinstall moviepy==1.0.3
    python -c "from moviepy.editor import VideoFileClip" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: MoviePy installation failed
        pause
        exit /b 1
    )
)

:: Check for port conflicts
echo [3/6] Checking for port conflicts...
netstat -an | find "8000" | find "LISTENING" >nul
if not errorlevel 1 (
    echo WARNING: Port 8000 in use, attempting to free it...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
)

netstat -an | find "5173" | find "LISTENING" >nul
if not errorlevel 1 (
    echo WARNING: Port 5173 in use, attempting to free it...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "5173" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
)

:: Start backend server
echo [4/6] Starting backend server...
echo Backend will be available at: http://localhost:8000
start "Video Editor Pro - Backend" cmd /k "title Video Editor Pro - Backend && cd backend && python main.py"

:: Wait for backend to initialize
echo [5/6] Waiting for backend to initialize...
timeout /t 15 /nobreak >nul

:: Test backend connection
echo Testing backend connection...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 3 | Out-Null; Write-Host 'Backend is responding' } catch { Write-Host 'Backend still starting...' }"

:: Start frontend server
echo [6/6] Starting frontend server...
echo Frontend will be available at: http://localhost:5173
start "Video Editor Pro - Frontend" cmd /k "title Video Editor Pro - Frontend && npm run dev"

:: Wait for frontend to initialize
echo Waiting for frontend to initialize...
timeout /t 12 /nobreak >nul

:: Open browser
echo Opening Video Editor Pro in browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================
echo    Video Editor Pro is now running!
echo ========================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Available features:
echo - Silence removal with auto-editor
echo - Background removal with BiRefNet AI
echo - Subtitle generation with Whisper AI
echo - Professional video player
echo - Multiple export formats
echo.
echo Press any key to stop all servers...
pause >nul

:: Stop all servers
echo.
echo Stopping servers...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

:: Stop processes on specific ports
for /f "tokens=5" %%a in ('netstat -ano ^| find "8000" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find "5173" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1

echo All servers stopped successfully
echo Thank you for using Video Editor Pro!
pause