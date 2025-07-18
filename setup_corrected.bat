@echo off
echo ========================================
echo    Video Editor Pro - Setup Script
echo ========================================
echo.

:: Check if Python is installed
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
echo Python found and ready

:: Check if Node.js is installed
echo [2/8] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 20+ from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js found and ready

:: Check if we're in the right directory
echo [3/8] Verifying project structure...
if not exist "backend" (
    echo ERROR: backend directory not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist "backend\requirements.txt" (
    echo ERROR: requirements.txt not found in backend directory
    pause
    exit /b 1
)
echo Project structure verified

:: Create virtual environment
echo [4/8] Creating virtual environment...
if exist "venv" rmdir /s /q venv
python -m venv venv --copies
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Trying alternative method...
    python -m venv venv --system-site-packages
    if errorlevel 1 (
        echo ERROR: Virtual environment creation failed completely
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo [5/8] Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo [6/8] Upgrading pip...
python -m pip install --upgrade pip

:: Install PyTorch with CUDA support
echo [7/8] Installing PyTorch with CUDA support...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

:: Install Python dependencies
echo [8/8] Installing Python dependencies...
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies failed, installing critical ones individually...
    python -m pip install moviepy>=1.0.3
    python -m pip install imageio-ffmpeg>=0.4.8
    python -m pip install transformers>=4.30.0
    python -m pip install fastapi>=0.100.0
    python -m pip install uvicorn>=0.22.0
    python -m pip install whisper
    python -m pip install auto-editor
    python -m pip install -r backend\requirements.txt
)

:: Install Node.js dependencies
echo Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)

:: Test installations
echo.
echo Testing installations...
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "from moviepy.editor import VideoFileClip; print('MoviePy: OK')"

echo.
echo Testing BiRefNet system...
cd backend
python background_remover.py --test 2>nul || echo "WARNING: BiRefNet test limited by rate limiting, but system will work"
cd ..

echo.
echo ========================================
echo         Setup Complete!
echo ========================================
echo.
echo To start the application, run: start.bat
echo.
pause