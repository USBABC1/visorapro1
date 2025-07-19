@echo off
echo ========================================
echo   Instalando Dependências Específicas
echo ========================================
echo.

:: Ativar ambiente virtual
call ..\venv\Scripts\activate.bat

echo [1/6] Instalando dependências de áudio avançadas...
python -m pip install librosa>=0.10.0
python -m pip install soundfile>=0.12.0
python -m pip install scipy>=1.10.0

echo [2/6] Instalando dlib para detecção facial...
python -m pip install dlib>=19.24.0 2>nul || (
    echo AVISO: dlib falhou, tentando com conda...
    conda install -c conda-forge dlib 2>nul || (
        echo AVISO: dlib não pôde ser instalado
        echo Redirecionamento de olhar funcionará apenas com OpenCV
    )
)

echo [3/6] Verificando Real-ESRGAN para upscaling...
where realesrgan-ncnn-vulkan >nul 2>&1 || (
    echo Real-ESRGAN não encontrado
    echo Baixando Real-ESRGAN...
    
    :: Criar diretório para Real-ESRGAN
    if not exist "realesrgan" mkdir realesrgan
    cd realesrgan
    
    :: Download Real-ESRGAN
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip' -OutFile 'realesrgan.zip'"
    
    if exist realesrgan.zip (
        echo Extraindo Real-ESRGAN...
        powershell -Command "Expand-Archive -Path 'realesrgan.zip' -DestinationPath '.'"
        del realesrgan.zip
        
        :: Adicionar ao PATH
        set "REALESRGAN_PATH=%CD%"
        setx PATH "%PATH%;%REALESRGAN_PATH%" /M >nul 2>&1
        
        echo ✓ Real-ESRGAN instalado com sucesso!
    ) else (
        echo ❌ Falha no download do Real-ESRGAN
        echo Upscaling funcionará apenas com OpenCV
    )
    
    cd ..
)

echo [4/6] Verificando Waifu2x...
where waifu2x-ncnn-vulkan >nul 2>&1 || (
    echo Waifu2x não encontrado
    echo Para melhor qualidade de upscaling, instale Waifu2x manualmente
    echo https://github.com/nihui/waifu2x-ncnn-vulkan/releases
)

echo [5/6] Baixando modelo de landmarks faciais...
cd backend
if not exist "shape_predictor_68_face_landmarks.dat" (
    echo Baixando modelo de landmarks faciais...
    powershell -Command "Invoke-WebRequest -Uri 'http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2' -OutFile 'landmarks.dat.bz2'"
    
    if exist landmarks.dat.bz2 (
        echo Extraindo modelo...
        python -c "import bz2; data=open('landmarks.dat.bz2','rb').read(); open('shape_predictor_68_face_landmarks.dat','wb').write(bz2.decompress(data))"
        del landmarks.dat.bz2
        echo ✓ Modelo de landmarks instalado!
    ) else (
        echo ❌ Falha no download do modelo de landmarks
        echo Redirecionamento de olhar funcionará com detecção básica
    )
)
cd ..

echo [6/6] Testando todas as funcionalidades...
cd backend

echo Testando remoção de background rápida...
python -c "from background_remover_fast import FastBackgroundRemover; print('✓ Background remover rápido OK')" || echo "❌ Background remover rápido falhou"

echo Testando editor de silêncio avançado...
python -c "from silence_remover_advanced import AdvancedSilenceRemover; print('✓ Editor de silêncio avançado OK')" || echo "❌ Editor de silêncio avançado falhou"

echo Testando upscaler Video2X...
python -c "from video_upscaler import Video2XUpscaler; print('✓ Video2X upscaler OK')" || echo "❌ Video2X upscaler falhou"

echo Testando redirecionador de olhar...
python -c "from gaze_redirector import GazeRedirector; print('✓ Gaze redirector OK')" || echo "❌ Gaze redirector falhou"

cd ..

echo.
echo ========================================
echo     Instalação de Dependências Concluída!
echo ========================================
echo.
echo ✅ Funcionalidades disponíveis:
echo    • Remoção de background ultra-rápida
echo    • Editor de silêncio com detecção de erros
echo    • Upscaling de vídeo com IA
echo    • Redirecionamento de olhar
echo.
echo ⚠️  Se alguma funcionalidade falhou:
echo    • Real-ESRGAN: Instale manualmente para melhor upscaling
echo    • dlib: Necessário para redirecionamento de olhar avançado
echo    • Waifu2x: Opcional para upscaling de anime
echo.
pause