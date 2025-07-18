@echo off
echo ========================================
echo    MoviePy Installation Fix
echo ========================================
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

echo [1/5] Updating pip...
python -m pip install --upgrade pip

echo [2/5] Installing imageio-ffmpeg first...
python -m pip install imageio-ffmpeg

echo [3/5] Installing MoviePy dependencies...
python -m pip install numpy>=1.24.0
python -m pip install imageio>=2.31.1
python -m pip install decorator>=4.4.2
python -m pip install tqdm>=4.65.0
python -m pip install requests>=2.31.0

echo [4/5] Installing MoviePy...
python -m pip install moviepy==1.0.3 --no-deps
python -m pip install moviepy==1.0.3

echo [5/5] Testing MoviePy installation...
python -c "from moviepy.editor import VideoFileClip; print('MoviePy installed successfully!')"

if errorlevel 1 (
    echo.
    echo MoviePy still failing. Trying alternative approach...
    echo.
    python -m pip uninstall moviepy -y
    python -m pip install --no-cache-dir moviepy==1.0.3
    python -c "from moviepy.editor import VideoFileClip; print('MoviePy installed successfully!')"
)

echo.
echo Testing complete. Press any key to continue...
pause