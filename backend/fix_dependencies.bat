@echo off
echo ========================================
echo    Corrigindo Dependências BiRefNet
echo ========================================
echo.

:: Activate virtual environment
call ..\venv\Scripts\activate.bat

echo [1/4] Instalando dependências faltantes...
python -m pip install einops>=0.6.0
python -m pip install kornia>=0.6.0
python -m pip install timm>=0.9.0
python -m pip install safetensors>=0.3.0

echo [2/4] Atualizando transformers...
python -m pip install --upgrade transformers>=4.30.0

echo [3/4] Atualizando huggingface_hub...
python -m pip install --upgrade huggingface_hub>=0.16.0

echo [4/4] Testando instalação...
python -c "import einops; print('✓ einops:', einops.__version__)"
python -c "import kornia; print('✓ kornia:', kornia.__version__)"
python -c "import timm; print('✓ timm:', timm.__version__)"

echo.
echo ✅ Dependências corrigidas!
echo O sistema agora usará métodos alternativos de alta qualidade
echo para evitar problemas de rate limiting do Hugging Face.
echo.
pause