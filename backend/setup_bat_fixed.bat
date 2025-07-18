@echo off
echo ========================================
echo    Video Editor Pro - Setup Script
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 20+ from https://nodejs.org/
    pause
    exit /b 1
)

:: Check if we're in the right directory
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

echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

echo [4/6] Installing PyTorch with CUDA support...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo [5/6] Installing Python dependencies...
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    echo Trying to install MoviePy separately...
    python -m pip install moviepy>=1.0.3
    python -m pip install imageio-ffmpeg>=0.4.8
    python -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo ERROR: Still failed to install dependencies
        pause
        exit /b 1
    )
)

echo [6/6] Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo.
echo Testing installations...
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "from moviepy.editor import VideoFileClip; print('MoviePy: OK')"

echo Testing BiRefNet authentication...
cd backend
python background_remover.py --test
cd ..

echo.
echo ========================================
echo         Setup Complete!
echo ========================================
echo.
echo To start the application, run: start.bat
echo.
pause