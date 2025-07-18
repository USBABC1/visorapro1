@echo off
title Video Editor Pro
color 0A
echo.
echo  ██╗   ██╗██╗██████╗ ███████╗ ██████╗     ███████╗██████╗ ██╗████████╗ ██████╗ ██████╗ 
echo  ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ██╔════╝██╔══██╗██║╚══██╔══╝██╔═══██╗██╔══██╗
echo  ██║   ██║██║██║  ██║█████╗  ██║   ██║    █████╗  ██║  ██║██║   ██║   ██║   ██║██████╔╝
echo  ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ██╔══╝  ██║  ██║██║   ██║   ██║   ██║██╔══██╗
echo   ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ███████╗██████╔╝██║   ██║   ╚██████╔╝██║  ██║
echo    ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚══════╝╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
echo.
echo ========================================
echo    Edição Profissional de Vídeo com IA
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

:: Check if backend directory exists
if not exist "backend" (
    echo ERROR: Backend directory not found
    echo Please ensure all files are in the correct location
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat

:: Check Python dependencies
echo [2/5] Checking dependencies...
python -c "import torch, transformers" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python dependencies not installed correctly
    echo Please run setup.bat again
    echo.
    pause
    exit /b 1
)

:: Check MoviePy specifically
python -c "from moviepy.editor import VideoFileClip" >nul 2>&1
if errorlevel 1 (
    echo ERROR: MoviePy not installed correctly
    echo Installing MoviePy...
    python -m pip install moviepy>=1.0.3
    python -c "from moviepy.editor import VideoFileClip" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Failed to install MoviePy
        pause
        exit /b 1
    )
)

:: Start backend server
echo [3/5] Starting backend server...
echo Backend will be available at: http://localhost:8000
start "Video Editor Pro - Backend" cmd /k "title Video Editor Pro - Backend && cd backend && python main.py"

:: Wait for backend to start
echo [4/5] Waiting for backend to initialize...
timeout /t 15 /nobreak >nul

:: Start frontend development server
echo [5/5] Starting frontend server...
echo Frontend will be available at: http://localhost:5173
start "Video Editor Pro - Frontend" cmd /k "title Video Editor Pro - Frontend && npm run dev"

:: Wait for frontend to start
echo Waiting for frontend to initialize...
timeout /t 10 /nobreak >nul

:: Open browser
echo Opening Video Editor Pro in your browser...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================
echo    Video Editor Pro is now running!
echo ========================================
echo.
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend:  http://localhost:8000
echo 📊 API Docs: http://localhost:8000/docs
echo.
echo Features available:
echo ✅ Silence removal with auto-editor
echo ✅ Background removal with BiRefNet AI
echo ✅ Subtitle generation with Whisper AI
echo ✅ Professional video player
echo ✅ Multiple export formats
echo.
echo Press any key to stop all servers...
pause >nul

:: Kill all related processes
echo.
echo Stopping servers...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

echo All servers stopped successfully.
echo Thank you for using Video Editor Pro!
echo.
pause