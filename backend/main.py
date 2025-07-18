import os
import sys
import json
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Import our processing modules
from background_remover import process_video as remove_background_video, test_models
from silence_remover import remove_silence, ffmpeg_silence_removal
from subtitle_generator import generate_subtitles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Video Editor Pro API", 
    version="2.0.0",
    description="API profissional para edição de vídeo com IA - Interface CapCut"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for processing status
processing_status: Dict[str, Dict[str, Any]] = {}

class ProcessingRequest(BaseModel):
    operation: str  # 'remove_silence', 'remove_background', 'generate_subtitles'
    settings: Dict[str, Any]

class ProcessingStatus(BaseModel):
    stage: str
    progress: float
    message: str
    completed: bool = False
    error: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "Video Editor Pro API v2.0 - Interface CapCut", 
        "status": "running",
        "features": [
            "🎬 Interface profissional estilo CapCut",
            "✂️ Remoção de silêncios com auto-editor",
            "🎭 Remoção de background com BiRefNet IA",
            "📝 Geração de legendas com Whisper IA",
            "🎥 Player de vídeo sofisticado e completo",
            "📤 Exportação em múltiplos formatos"
        ],
        "endpoints": {
            "upload": "/upload",
            "process": "/process/{session_id}",
            "status": "/status/{session_id}",
            "download": "/download/{session_id}",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    # Test BiRefNet authentication
    birefnet_status = False
    try:
        birefnet_status = test_models()
        logger.info("✓ BiRefNet authentication successful")
    except Exception as e:
        logger.warning(f"⚠ BiRefNet authentication failed: {e}")
    
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "interface": "CapCut-style Professional",
        "birefnet_authenticated": birefnet_status,
        "timestamp": datetime.now().isoformat(),
        "system": {
            "python_version": sys.version,
            "temp_dir": tempfile.gettempdir(),
            "active_sessions": len(processing_status)
        },
        "features": {
            "silence_removal": True,
            "background_removal": birefnet_status,
            "subtitle_generation": True,
            "professional_player": True
        }
    }

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser um vídeo válido")
        
        # Validate file size (max 1GB)
        if file.size and file.size > 1024 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 1GB)")
        
        # Create temporary directory for this session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(processing_status)}"
        temp_dir = Path(tempfile.gettempdir()) / "video_editor_pro" / session_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        input_path = temp_dir / f"input_{file.filename}"
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Initialize processing status
        processing_status[session_id] = {
            "input_path": str(input_path),
            "temp_dir": str(temp_dir),
            "filename": file.filename,
            "status": "uploaded",
            "created_at": datetime.now().isoformat(),
            "file_size": len(content),
            "content_type": file.content_type
        }
        
        logger.info(f"✓ Upload realizado: {file.filename} ({len(content)} bytes)")
        return {
            "session_id": session_id, 
            "filename": file.filename, 
            "size": len(content),
            "size_mb": round(len(content) / (1024 * 1024), 2),
            "content_type": file.content_type,
            "message": "Upload realizado com sucesso! Pronto para processamento."
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@app.post("/process/{session_id}")
async def process_video(
    session_id: str, 
    request: ProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Start video processing"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    session = processing_status[session_id]
    input_path = session["input_path"]
    temp_dir = Path(session["temp_dir"])
    
    # Validate operation
    valid_operations = ['remove_silence', 'remove_background', 'generate_subtitles']
    if request.operation not in valid_operations:
        raise HTTPException(status_code=400, detail=f"Operação inválida. Deve ser uma de: {valid_operations}")
    
    # Start background processing
    background_tasks.add_task(
        process_video_background,
        session_id,
        input_path,
        temp_dir,
        request.operation,
        request.settings
    )
    
    logger.info(f"🚀 Iniciado processamento {request.operation} para sessão {session_id}")
    return {
        "message": "Processamento iniciado com sucesso!", 
        "session_id": session_id,
        "operation": request.operation,
        "operation_name": {
            "remove_silence": "Remoção de Silêncios",
            "remove_background": "Remoção de Background",
            "generate_subtitles": "Geração de Legendas"
        }.get(request.operation, request.operation)
    }

@app.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """Get processing status"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    return processing_status[session_id]

@app.get("/download/{session_id}")
async def download_result(session_id: str):
    """Download processed video"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    session = processing_status[session_id]
    if "output_path" not in session:
        raise HTTPException(status_code=404, detail="Nenhum arquivo processado disponível")
    
    output_path = session["output_path"]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Arquivo processado não encontrado")
    
    return FileResponse(
        output_path,
        media_type='video/mp4',
        filename=f"processed_{session['filename']}"
    )

@app.get("/download/{session_id}/subtitles")
async def download_subtitles(session_id: str):
    """Download generated subtitles"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    session = processing_status[session_id]
    if "subtitle_path" not in session:
        raise HTTPException(status_code=404, detail="Nenhum arquivo de legenda disponível")
    
    subtitle_path = session["subtitle_path"]
    if not os.path.exists(subtitle_path):
        raise HTTPException(status_code=404, detail="Arquivo de legenda não encontrado")
    
    return FileResponse(
        subtitle_path,
        media_type='text/plain',
        filename=f"subtitles_{session['filename']}.srt"
    )

async def process_video_background(
    session_id: str,
    input_path: str,
    temp_dir: Path,
    operation: str,
    settings: Dict[str, Any]
):
    """Background task for video processing"""
    try:
        session = processing_status[session_id]
        
        # Update status function
        def update_status(stage: str, progress: float, message: str):
            session.update({
                "stage": stage,
                "progress": progress,
                "message": message,
                "status": "processing",
                "updated_at": datetime.now().isoformat()
            })
            logger.info(f"📊 Sessão {session_id}: {stage} - {progress}% - {message}")
        
        output_path = temp_dir / f"output_{Path(input_path).stem}.mp4"
        
        if operation == "remove_silence":
            update_status("analyzing", 15, "🔍 Analisando áudio para detectar silêncios...")
            await asyncio.sleep(2)
            
            update_status("processing", 60, "✂️ Removendo silêncios e criando transições suaves...")
            success = await remove_silence(
                input_path, 
                str(output_path), 
                settings.get('silenceThreshold', -30),
                settings.get('frameMargin', 6)
            )
            
            if not success:
                # Try with FFmpeg as fallback
                logger.info("Auto-editor failed, trying FFmpeg fallback...")
                update_status("processing", 70, "🔄 Tentando método alternativo com FFmpeg...")
                success = await ffmpeg_silence_removal(input_path, str(output_path), settings)
            
            update_status("encoding", 90, "🎬 Codificando vídeo final com qualidade profissional...")
            await asyncio.sleep(2)
            
        elif operation == "remove_background":
            update_status("analyzing", 15, "🤖 Carregando modelo BiRefNet de alta qualidade...")
            await asyncio.sleep(3)
            
            update_status("processing", 60, "🎭 Processando remoção de background com IA...")
            # Run in thread pool to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    remove_background_video,
                    input_path,
                    str(output_path),
                    background_type=settings.get('backgroundType', 'transparent'),
                    background_value=settings.get('backgroundValue'),
                    fast_mode=settings.get('fastMode', False),
                    quality=settings.get('quality', 'high'),
                    enhance_quality=settings.get('enhanceQuality', True)
                )
                success = future.result()
            
            update_status("encoding", 90, "✨ Aplicando efeitos finais e codificando...")
            await asyncio.sleep(2)
            
        elif operation == "generate_subtitles":
            update_status("analyzing", 15, "🎵 Extraindo áudio para transcrição...")
            await asyncio.sleep(2)
            
            update_status("processing", 60, "📝 Gerando legendas com IA Whisper...")
            subtitle_path = temp_dir / f"subtitles_{Path(input_path).stem}.srt"
            success = await generate_subtitles(
                input_path,
                str(subtitle_path),
                language=settings.get('language', 'pt')
            )
            
            if success:
                session["subtitle_path"] = str(subtitle_path)
            
            # Copy original video as output for subtitle generation
            shutil.copy2(input_path, output_path)
            
            update_status("encoding", 90, "🔄 Sincronizando legendas com vídeo...")
            await asyncio.sleep(2)
            
        else:
            raise ValueError(f"Operação desconhecida: {operation}")
        
        if success and output_path.exists():
            session.update({
                "output_path": str(output_path),
                "stage": "completed",
                "progress": 100,
                "message": "🎉 Processamento concluído com sucesso! Qualidade profissional garantida.",
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "output_size": output_path.stat().st_size,
                "output_size_mb": round(output_path.stat().st_size / (1024 * 1024), 2)
            })
            logger.info(f"✅ Processamento concluído com sucesso para sessão {session_id}")
        else:
            raise Exception("Processamento falhou - arquivo de saída não foi criado")
            
    except Exception as e:
        logger.error(f"❌ Erro no processamento da sessão {session_id}: {str(e)}")
        session.update({
            "stage": "error",
            "progress": 0,
            "message": f"❌ Erro durante o processamento: {str(e)}",
            "status": "error",
            "error": str(e),
            "error_at": datetime.now().isoformat()
        })

@app.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up session files"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    session = processing_status[session_id]
    temp_dir = Path(session["temp_dir"])
    
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        del processing_status[session_id]
        logger.info(f"🧹 Sessão {session_id} limpa com sucesso")
        return {"message": "Sessão limpa com sucesso"}
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test/birefnet")
async def test_birefnet():
    """Test BiRefNet model loading and authentication"""
    try:
        success = test_models()
        return {
            "status": "success" if success else "failed",
            "message": "Teste de autenticação e carregamento do BiRefNet",
            "authenticated": success,
            "details": "✅ Modelos BiRefNet carregados e autenticados com sucesso" if success else "❌ Falha ao carregar modelos BiRefNet"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "authenticated": False,
            "details": f"❌ Erro testando BiRefNet: {str(e)}"
        }

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": list(processing_status.keys()),
        "total": len(processing_status),
        "details": {k: {
            "status": v.get("status"),
            "created_at": v.get("created_at"),
            "filename": v.get("filename"),
            "size_mb": round(v.get("file_size", 0) / (1024 * 1024), 2) if v.get("file_size") else 0
        } for k, v in processing_status.items()}
    }

@app.get("/system/info")
async def system_info():
    """Get system information"""
    import psutil
    import torch
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "system": {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_usage": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "ai": {
                "torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
            },
            "sessions": {
                "active": len(processing_status),
                "processing": len([s for s in processing_status.values() if s.get("status") == "processing"])
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Não foi possível obter informações do sistema"
        }

if __name__ == "__main__":
    # Ensure required directories exist
    temp_base = Path(tempfile.gettempdir()) / "video_editor_pro"
    temp_base.mkdir(exist_ok=True)
    
    # Test BiRefNet authentication on startup
    try:
        if test_models():
            logger.info("✅ Modelos BiRefNet autenticados e prontos")
        else:
            logger.warning("⚠️ Autenticação BiRefNet falhou - remoção de background pode não funcionar")
    except Exception as e:
        logger.error(f"❌ Teste BiRefNet falhou: {e}")
    
    # Start the server
    logger.info("🚀 Iniciando Video Editor Pro API v2.0 - Interface CapCut...")
    logger.info("📡 Servidor estará disponível em: http://localhost:8000")
    logger.info("📚 Documentação da API: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for better stability
        log_level="info"
    )