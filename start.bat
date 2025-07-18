@echo off
title Video Editor Pro - Inicializador
color 0A
echo.
echo ========================================
echo    Video Editor Pro - Inicializando
echo ========================================
echo.

:: Verificar se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERRO: Ambiente virtual não encontrado
    echo.
    echo 🔧 Execute primeiro: setup.bat
    echo.
    pause
    exit /b 1
)

:: Verificar se o diretório backend existe
if not exist "backend" (
    echo ❌ ERRO: Diretório backend não encontrado
    echo.
    echo 📁 Certifique-se de estar no diretório correto do projeto
    echo.
    pause
    exit /b 1
)

:: Ativar ambiente virtual
echo [1/8] 🐍 Ativando ambiente virtual Python...
call venv\Scripts\activate.bat

:: Verificar dependências críticas
echo [2/8] 🔍 Verificando dependências...
python -c "import torch, transformers, fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Dependências Python não instaladas corretamente
    echo.
    echo 🔧 Execute novamente: setup.bat
    echo.
    pause
    exit /b 1
)

:: Verificar MoviePy especificamente
python -c "from moviepy.editor import VideoFileClip" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  MoviePy com problemas, reinstalando...
    python -m pip install --force-reinstall moviepy==1.0.3
    python -c "from moviepy.editor import VideoFileClip" >nul 2>&1
    if errorlevel 1 (
        echo ❌ ERRO: MoviePy não funciona corretamente
        echo.
        echo 🔧 Execute: setup.bat novamente
        pause
        exit /b 1
    )
)

echo ✅ Dependências verificadas

:: Verificar se as portas estão livres
echo [3/8] 🌐 Verificando portas disponíveis...
netstat -an | find "8000" | find "LISTENING" >nul
if not errorlevel 1 (
    echo ⚠️  Porta 8000 em uso, tentando finalizar processo...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

netstat -an | find "5173" | find "LISTENING" >nul
if not errorlevel 1 (
    echo ⚠️  Porta 5173 em uso, tentando finalizar processo...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "5173" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: Configurar Hugging Face se necessário
echo [4/8] 🤖 Verificando configuração Hugging Face...
cd backend
python huggingface_setup.py
cd ..

:: Testar sistema de background removal
echo [5/8] 🧪 Testando sistema de IA...
cd backend
python background_remover.py --test >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Sistema BiRefNet com limitações, mas métodos alternativos disponíveis
) else (
    echo ✅ Sistema de IA funcionando perfeitamente
)
cd ..

:: Iniciar servidor backend
echo [6/8] 🚀 Iniciando servidor backend...
echo    Backend estará disponível em: http://localhost:8000
start "Video Editor Pro - Backend" cmd /k "title Video Editor Pro - Backend API && color 0B && cd backend && python main.py"

:: Aguardar backend inicializar
echo [7/8] ⏳ Aguardando backend inicializar...
timeout /t 15 /nobreak >nul

:: Testar conexão com backend
echo Testando conexão com backend...
:test_backend
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { Write-Host '✅ Backend respondendo' } else { Write-Host '⚠️ Backend com problemas' } } catch { Write-Host '⏳ Backend ainda inicializando...' }"

:: Verificar se backend está realmente funcionando
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo ⏳ Aguardando mais um pouco...
    timeout /t 10 /nobreak >nul
    goto test_backend
)

:: Iniciar servidor frontend
echo [8/8] 🎨 Iniciando servidor frontend...
echo    Frontend estará disponível em: http://localhost:5173
start "Video Editor Pro - Frontend" cmd /k "title Video Editor Pro - Interface && color 0E && npm run dev"

:: Aguardar frontend inicializar
echo ⏳ Aguardando frontend inicializar...
timeout /t 12 /nobreak >nul

:: Abrir navegador
echo 🌐 Abrindo Video Editor Pro no navegador...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================
echo    🎉 VIDEO EDITOR PRO ESTÁ RODANDO! 🎉
echo ========================================
echo.
echo 🌐 Interface:     http://localhost:5173
echo 🔧 API Backend:   http://localhost:8000
echo 📚 Documentação:  http://localhost:8000/docs
echo.
echo 🎬 RECURSOS DISPONÍVEIS:
echo ✅ Interface profissional estilo CapCut
echo ✅ Player de vídeo sofisticado e completo
echo ✅ Remoção automática de silêncios (auto-editor)
echo ✅ Remoção de background com IA + métodos alternativos
echo ✅ Geração de legendas sincronizadas (Whisper)
echo ✅ Exportação em múltiplos formatos
echo ✅ Configurações avançadas de qualidade
echo.
echo 📋 COMO USAR:
echo 1. Arraste um vídeo para a interface
echo 2. Escolha a ferramenta desejada
echo 3. Configure as opções avançadas
echo 4. Clique em "Processar Agora"
echo 5. Baixe o resultado processado
echo.
echo 💡 DICAS:
echo • Use "Alta Qualidade" para resultados profissionais
echo • Configure o limite de silêncio conforme necessário
echo • Experimente diferentes backgrounds na remoção de fundo
echo • Legendas são exportadas em formato SRT
echo • Sistema funciona mesmo sem token Hugging Face
echo.
echo ⚠️  Para parar todos os servidores, pressione qualquer tecla...
pause >nul

:: Finalizar todos os processos
echo.
echo 🛑 Finalizando servidores...

:: Finalizar processos Python e Node
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

:: Finalizar janelas específicas
for /f "tokens=2" %%i in ('tasklist /fi "windowtitle eq Video Editor Pro - Backend API" /fo csv 2^>nul ^| find "cmd.exe"') do taskkill /f /pid %%i >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /fi "windowtitle eq Video Editor Pro - Interface" /fo csv 2^>nul ^| find "cmd.exe"') do taskkill /f /pid %%i >nul 2>&1

:: Finalizar processos nas portas específicas
for /f "tokens=5" %%a in ('netstat -ano ^| find "8000" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find "5173" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1

echo ✅ Todos os servidores foram finalizados com sucesso
echo.
echo 🙏 Obrigado por usar o Video Editor Pro!
echo    Desenvolvido com ❤️ para criadores de conteúdo
echo.
echo 💡 NOTA: Sistema funciona com ou sem token Hugging Face
echo    Métodos alternativos garantem qualidade profissional
echo.
pause