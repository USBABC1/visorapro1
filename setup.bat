@echo off
title Video Editor Pro - Setup Completo
color 0A
echo.
echo ========================================
echo    Video Editor Pro - Setup Automático
echo ========================================
echo.

:: Verificar se está executando como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo AVISO: Execute como Administrador para melhor compatibilidade
    echo Continuando com instalação limitada...
    echo.
)

:: Verificar se Python está instalado
echo [1/12] Verificando Python...
where python >nul 2>&1
if errorlevel 1 (
    echo Python não encontrado. Instalando Python 3.11...
    echo.
    
    :: Download e instalação do Python
    echo Baixando Python 3.11.7...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile 'python_installer.exe'}"
    
    if exist python_installer.exe (
        echo Instalando Python...
        python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del python_installer.exe
        
        :: Atualizar PATH
        set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
        
        echo Python instalado com sucesso!
    ) else (
        echo ERRO: Falha no download do Python
        echo Por favor, instale manualmente: https://www.python.org/downloads/
        pause
        exit /b 1
    )
) else (
    echo ✓ Python encontrado
)

:: Verificar se Node.js está instalado
echo [2/12] Verificando Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo Node.js não encontrado. Instalando Node.js 20...
    echo.
    
    :: Download e instalação do Node.js
    echo Baixando Node.js 20.10.0...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi' -OutFile 'nodejs_installer.msi'}"
    
    if exist nodejs_installer.msi (
        echo Instalando Node.js...
        msiexec /i nodejs_installer.msi /quiet
        del nodejs_installer.msi
        
        :: Atualizar PATH
        set "PATH=%PATH%;C:\Program Files\nodejs"
        
        echo Node.js instalado com sucesso!
    ) else (
        echo ERRO: Falha no download do Node.js
        echo Por favor, instale manualmente: https://nodejs.org/
        pause
        exit /b 1
    )
) else (
    echo ✓ Node.js encontrado
)

:: Verificar se FFmpeg está instalado
echo [3/12] Verificando FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo FFmpeg não encontrado. Instalando FFmpeg...
    echo.
    
    :: Criar diretório para FFmpeg
    if not exist "ffmpeg" mkdir ffmpeg
    cd ffmpeg
    
    :: Download do FFmpeg
    echo Baixando FFmpeg...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'}"
    
    if exist ffmpeg.zip (
        echo Extraindo FFmpeg...
        powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.'"
        
        :: Mover arquivos para local correto
        for /d %%i in (ffmpeg-master-latest-win64-gpl) do (
            move "%%i\bin\*.exe" .
            rmdir /s /q "%%i"
        )
        del ffmpeg.zip
        
        :: Adicionar ao PATH
        set "FFMPEG_PATH=%CD%"
        setx PATH "%PATH%;%FFMPEG_PATH%" /M >nul 2>&1
        
        cd ..
        echo ✓ FFmpeg instalado com sucesso!
    ) else (
        cd ..
        echo ERRO: Falha no download do FFmpeg
        echo Continuando sem FFmpeg (funcionalidade limitada)
    )
) else (
    echo ✓ FFmpeg encontrado
)

:: Verificar diretórios necessários
echo [4/12] Verificando estrutura do projeto...
if not exist "backend" (
    echo ERRO: Diretório backend não encontrado
    echo Certifique-se de estar no diretório correto do projeto
    pause
    exit /b 1
)

if not exist "backend\requirements.txt" (
    echo ERRO: requirements.txt não encontrado
    echo Certifique-se de que todos os arquivos estão presentes
    pause
    exit /b 1
)

echo ✓ Estrutura do projeto verificada

:: Criar ambiente virtual Python
echo [5/12] Criando ambiente virtual Python...
python -m venv venv
if errorlevel 1 (
    echo ERRO: Falha ao criar ambiente virtual
    pause
    exit /b 1
)

echo ✓ Ambiente virtual criado

:: Ativar ambiente virtual
echo [6/12] Ativando ambiente virtual...
call venv\Scripts\activate.bat

:: Atualizar pip
echo [7/12] Atualizando pip...
python -m pip install --upgrade pip

:: Instalar PyTorch com suporte CUDA
echo [8/12] Instalando PyTorch com suporte CUDA...
echo Isso pode demorar alguns minutos...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

:: Instalar dependências específicas primeiro
echo [9/12] Instalando dependências críticas...
python -m pip install einops>=0.6.0
python -m pip install kornia>=0.6.0
python -m pip install timm>=0.9.0
python -m pip install moviepy==1.0.3
python -m pip install imageio==2.31.1
python -m pip install imageio-ffmpeg==0.4.8
python -m pip install "numpy>=1.24.0"
python -m pip install "opencv-python>=4.7.0"

:: Instalar todas as dependências Python
echo [10/12] Instalando dependências Python...
python -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo AVISO: Algumas dependências falharam, tentando instalação individual...
    
    :: Tentar instalar dependências críticas individualmente
    python -m pip install "transformers>=4.30.0"
    python -m pip install "huggingface_hub>=0.16.0"
    python -m pip install "accelerate>=0.20.0"
    python -m pip install "openai-whisper>=20230314"
    python -m pip install "fastapi>=0.100.0"
    python -m pip install "uvicorn>=0.22.0"
    python -m pip install "python-multipart>=0.0.6"
    python -m pip install "aiofiles>=23.1.0"
    python -m pip install "auto-editor>=23.0.0"
)

:: Instalar dependências Node.js
echo [11/12] Instalando dependências Node.js...
npm install
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependências Node.js
    echo Tentando com cache limpo...
    npm cache clean --force
    npm install
    if errorlevel 1 (
        echo ERRO: Falha persistente nas dependências Node.js
        pause
        exit /b 1
    )
)

:: Testar instalações
echo [12/12] Testando instalações...

echo Testando Python e módulos...
python -c "import torch; print(f'✓ PyTorch: {torch.__version__}')" 2>nul || echo "⚠ PyTorch: Erro"
python -c "import transformers; print(f'✓ Transformers: {transformers.__version__}')" 2>nul || echo "⚠ Transformers: Erro"
python -c "from moviepy.editor import VideoFileClip; print('✓ MoviePy: OK')" 2>nul || echo "⚠ MoviePy: Erro"
python -c "import whisper; print('✓ Whisper: OK')" 2>nul || (
    echo "Instalando Whisper..."
    python -m pip install openai-whisper
)

echo Testando auto-editor...
where auto-editor >nul 2>&1 || (
    echo "Instalando auto-editor..."
    python -m pip install auto-editor
)

echo Testando sistema de background removal...
cd backend
python background_remover.py --test
cd ..

echo.
echo ========================================
echo         INSTALAÇÃO CONCLUÍDA!
echo ========================================
echo.
echo ✅ Componentes instalados:
echo    • Python 3.11+ com ambiente virtual
echo    • Node.js 20+ com npm
echo    • FFmpeg para processamento de vídeo
echo    • PyTorch com suporte CUDA
echo    • Auto-editor para remoção de silêncios
echo    • Whisper IA para geração de legendas
echo    • BiRefNet IA com métodos alternativos
echo    • Todas as dependências necessárias
echo.
echo 🚀 Para iniciar o aplicativo, execute: start.bat
echo.
echo 📋 Recursos disponíveis:
echo    • Interface profissional estilo CapCut
echo    • Player de vídeo sofisticado e completo
echo    • Remoção automática de silêncios
echo    • Remoção de background com IA + métodos alternativos
echo    • Geração de legendas sincronizadas
echo    • Exportação em múltiplos formatos
echo.
echo ⚠️  IMPORTANTE: 
echo    • Se instalou Python/Node.js pela primeira vez, reinicie o prompt
echo    • O sistema funciona mesmo sem token Hugging Face
echo    • Métodos alternativos garantem funcionamento completo
echo.
pause