import React, { useState, useCallback, useRef } from 'react';
import { Upload, Play, Pause, Volume2, Settings, Download, Subtitles, Scissors, Eraser, Sparkles, FileVideo, Zap, AlertCircle, CheckCircle, Loader2, Monitor, Cpu, HardDrive, X, Maximize2, SkipBack, SkipForward, RotateCcw } from 'lucide-react';
import VideoPlayer from './components/VideoPlayer';
import ProcessingModal from './components/ProcessingModal';
import SettingsModal from './components/SettingsModal';
import BackgroundRemovalSettings from './components/BackgroundRemovalSettings';
import SystemStatus from './components/SystemStatus';
import { ProcessingSettings, ProcessingStatus, VideoFile } from './types';

const App: React.FC = () => {
  // State management
  const [originalVideo, setOriginalVideo] = useState<VideoFile | null>(null);
  const [processedVideo, setProcessedVideo] = useState<string | null>(null);
  const [subtitleFile, setSubtitleFile] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    stage: 'idle',
    progress: 0,
    message: 'Aguardando...'
  });
  const [showSettings, setShowSettings] = useState(false);
  const [activeOperation, setActiveOperation] = useState<'remove_silence' | 'remove_background' | 'generate_subtitles' | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [dragActive, setDragActive] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Default settings
  const [settings, setSettings] = useState<ProcessingSettings>({
    silenceThreshold: -30,
    frameMargin: 6,
    videoQuality: 23,
    resolution: 'original',
    videoCodec: 'h264',
    exportFormat: 'mp4',
    enableSubtitles: true,
    subtitleLanguage: 'pt-BR'
  });

  // Background removal settings
  const [backgroundSettings, setBackgroundSettings] = useState({
    fastMode: false,
    quality: 'high' as 'low' | 'medium' | 'high',
    enhanceQuality: true,
    backgroundType: 'transparent' as 'transparent' | 'color' | 'image',
    backgroundColor: '#00FF00',
    backgroundImage: null as string | null
  });

  // Check backend availability
  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      const data = await response.json();
      setBackendAvailable(response.ok && data.birefnet_authenticated);
      return response.ok;
    } catch (error) {
      console.error('Backend not available:', error);
      setBackendAvailable(false);
      return false;
    }
  };

  // File upload handler
  const handleFileUpload = useCallback(async (file: File) => {
    try {
      const backendOk = await checkBackendStatus();
      if (!backendOk) {
        alert('Backend não está disponível. Execute start.bat para iniciar o servidor.');
        return;
      }

      const url = URL.createObjectURL(file);
      const video = document.createElement('video');
      
      video.onloadedmetadata = () => {
        const videoFile: VideoFile = {
          file,
          url,
          duration: video.duration,
          size: file.size,
          format: file.type
        };
        setOriginalVideo(videoFile);
        setProcessedVideo(null);
        setSubtitleFile(null);
      };
      
      video.src = url;

      // Upload to backend
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(60000)
      });

      if (response.ok) {
        const result = await response.json();
        setSessionId(result.session_id);
        setBackendAvailable(true);
      } else {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Erro no upload:', error);
      
      let errorMessage = 'Erro ao carregar o vídeo.';
      
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        errorMessage = 'Não foi possível conectar ao servidor. Execute start.bat para iniciar o backend.';
      } else if (error instanceof Error && error.name === 'AbortError') {
        errorMessage = 'Upload cancelado por timeout. Tente um arquivo menor.';
      } else if (error instanceof Error) {
        errorMessage = `Erro: ${error.message}`;
      }
      
      alert(errorMessage);
      setBackendAvailable(false);
    }
  }, []);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    const videoFile = files.find(file => file.type.startsWith('video/'));
    
    if (videoFile) {
      handleFileUpload(videoFile);
    } else {
      alert('Por favor, selecione um arquivo de vídeo válido.');
    }
  }, [handleFileUpload]);

  // Processing functions
  const startProcessing = async (operation: 'remove_silence' | 'remove_background' | 'generate_subtitles') => {
  const startProcessing = async (operation: 'remove_silence' | 'remove_background' | 'generate_subtitles' | 'upscale_video' | 'redirect_gaze') => {
    if (!sessionId) {
      alert('Por favor, carregue um vídeo primeiro.');
      return;
    }

    const backendOk = await checkBackendStatus();
    if (!backendOk) {
      alert('Backend não está disponível. Execute start.bat para iniciar o servidor.');
      return;
    }

    setActiveOperation(operation);
    setIsProcessing(true);
    setProcessingStatus({
      stage: 'analyzing',
      progress: 10,
      message: 'Iniciando processamento...'
    });

    try {
      let requestSettings = {};
      
      if (operation === 'remove_silence') {
        requestSettings = {
          silenceThreshold: settings.silenceThreshold,
          frameMargin: settings.frameMargin
        };
      } else if (operation === 'remove_background') {
        requestSettings = {
          ...backgroundSettings,
          backgroundValue: backgroundSettings.backgroundType === 'color' 
            ? backgroundSettings.backgroundColor 
            : backgroundSettings.backgroundImage
        };
      } else if (operation === 'generate_subtitles') {
        requestSettings = {
          language: settings.subtitleLanguage.split('-')[0]
        };
      } else if (operation === 'upscale_video') {
        requestSettings = {
          scaleFactor: 2, // Default 2x upscaling
          model: 'auto',
          quality: 'high'
        };
      } else if (operation === 'redirect_gaze') {
        requestSettings = {
          targetDirection: 0.0 // Look at camera (center)
        };
      }

      // Start processing
      const response = await fetch(`http://localhost:8000/process/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          operation,
          settings: requestSettings
        }),
        signal: AbortSignal.timeout(10000)
      });

      if (!response.ok) {
        throw new Error(`Falha ao iniciar processamento: ${response.status} ${response.statusText}`);
      }

      // Poll for status updates
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/status/${sessionId}`, {
            signal: AbortSignal.timeout(5000)
          });
          
          if (statusResponse.ok) {
            const status = await statusResponse.json();
            
            setProcessingStatus({
              stage: status.stage || 'processing',
              progress: status.progress || 0,
              message: status.message || 'Processando...'
            });

            if (status.status === 'completed') {
              setProcessedVideo(`http://localhost:8000/download/${sessionId}`);
              if (operation === 'generate_subtitles') {
                setSubtitleFile(`http://localhost:8000/download/${sessionId}/subtitles`);
              }
              setIsProcessing(false);
              setBackendAvailable(true);
            } else if (status.status === 'error') {
              setProcessingStatus({
                stage: 'error',
                progress: 0,
                message: status.error || 'Erro durante o processamento'
              });
              setIsProcessing(false);
            } else {
              setTimeout(pollStatus, 1000);
            }
          } else {
            throw new Error(`Status check failed: ${statusResponse.status}`);
          }
        } catch (error) {
          console.error('Erro ao verificar status:', error);
          if (error instanceof Error && error.name === 'AbortError') {
            setBackendAvailable(false);
          }
          setTimeout(pollStatus, 2000);
        }
      };

      setTimeout(pollStatus, 1000);

    } catch (error) {
      console.error('Erro no processamento:', error);
      
      let errorMessage = 'Erro ao processar vídeo';
      
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        errorMessage = 'Conexão com o servidor perdida durante o processamento';
        setBackendAvailable(false);
      } else if (error instanceof Error && error.name === 'AbortError') {
        errorMessage = 'Processamento cancelado por timeout';
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      setProcessingStatus({
        stage: 'error',
        progress: 0,
        message: errorMessage
      });
      setIsProcessing(false);
    }
  };

  // Download handlers
  const downloadVideo = () => {
    if (processedVideo && sessionId) {
      const link = document.createElement('a');
      link.href = processedVideo;
      link.download = `processed_${originalVideo?.file.name || 'video'}.${settings.exportFormat}`;
      link.click();
    }
  };

  const downloadSubtitles = () => {
    if (subtitleFile && sessionId) {
      const link = document.createElement('a');
      link.href = subtitleFile;
      link.download = `subtitles_${originalVideo?.file.name || 'video'}.srt`;
      link.click();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white overflow-hidden">
      {/* CapCut-style Header */}
      <header className="glass-morphism border-b border-white/10 sticky top-0 z-40 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-2xl animate-gradient-shift">
                <FileVideo className="w-7 h-7 text-white drop-shadow-lg" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent animate-gradient-shift">
                  Video Editor Pro
                </h1>
                <p className="text-sm text-gray-400 font-medium">Edição profissional com IA • Qualidade CapCut</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <SystemStatus backendAvailable={backendAvailable} onRefresh={checkBackendStatus} />
              
              <button
                onClick={() => setShowSettings(true)}
                className="neumorphic-button p-3 rounded-xl hover:bg-white/10 transition-all duration-300 group"
                title="Configurações Avançadas"
              >
                <Settings className="w-5 h-5 text-gray-300 group-hover:text-white group-hover:rotate-90 transition-all duration-300" />
              </button>
              
              {processedVideo && (
                <div className="flex items-center space-x-3">
                  <button
                    onClick={downloadVideo}
                    className="export-button modern-button bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 px-6 py-3 rounded-xl font-medium transition-all duration-300 flex items-center space-x-2 shadow-lg hover:shadow-green-500/25 hover:scale-105"
                  >
                    <Download className="w-5 h-5" />
                    <span>Download Vídeo</span>
                  </button>
                  
                  {subtitleFile && (
                    <button
                      onClick={downloadSubtitles}
                      className="export-button modern-button bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 px-4 py-3 rounded-xl font-medium transition-all duration-300 flex items-center space-x-2 shadow-lg hover:shadow-yellow-500/25 hover:scale-105"
                    >
                      <Subtitles className="w-5 h-5" />
                      <span>SRT</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* CapCut-style Upload Area */}
        {!originalVideo && (
          <div className="relative">
            <div
              className={`glass-morphism rounded-3xl p-16 text-center border-2 border-dashed transition-all duration-500 cursor-pointer group relative overflow-hidden ${
                dragActive 
                  ? 'border-blue-500 bg-blue-500/10 scale-105' 
                  : backendAvailable 
                    ? 'border-white/20 hover:border-blue-500/50 hover:bg-blue-500/5' 
                    : 'border-red-500/30 hover:border-red-500/50 hover:bg-red-500/5'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => backendAvailable && fileInputRef.current?.click()}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-purple-600/5 to-pink-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              
              <div className={`relative z-10 w-32 h-32 rounded-full flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-all duration-500 ${
                backendAvailable 
                  ? 'bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 animate-pulse-glow' 
                  : 'bg-gradient-to-r from-red-500/20 to-red-500/20'
              }`}>
                <Upload className={`w-16 h-16 ${backendAvailable ? 'text-blue-400' : 'text-red-400'} drop-shadow-lg ${dragActive ? 'animate-bounce' : ''}`} />
              </div>
              
              <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                {dragActive ? 'Solte o vídeo aqui!' : backendAvailable ? 'Arraste seu vídeo aqui' : 'Backend não disponível'}
              </h2>
              
              <p className="text-gray-400 mb-8 text-lg">
                {backendAvailable 
                  ? 'Ou clique para selecionar um arquivo • Máxima qualidade garantida'
                  : 'Execute start.bat para iniciar o servidor'
                }
              </p>
              
              {backendAvailable && (
                <div className="flex flex-wrap justify-center gap-3 text-sm">
                  {['MP4', 'MOV', 'AVI', 'MKV', 'WEBM'].map((format) => (
                    <span key={format} className="px-4 py-2 bg-gray-800/50 rounded-full border border-gray-600/50 hover:border-blue-500/50 transition-colors duration-300">
                      {format}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
              className="hidden"
            />
          </div>
        )}

        {/* CapCut-style Video Players */}
        {originalVideo && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <VideoPlayer
              src={originalVideo.url}
              title="Vídeo Original"
              isOriginal={true}
            />
            <VideoPlayer
              src={processedVideo}
              title="Vídeo Processado"
              isOriginal={false}
            />
          </div>
        )}

        {/* Enhanced Processing Tools */}
        {originalVideo && (
          <div className="glass-morphism rounded-3xl p-8 shadow-2xl border border-white/10 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-purple-600/5 to-pink-600/5"></div>
            
            <div className="relative z-10">
              <h2 className="text-3xl font-bold mb-8 flex items-center">
                <Sparkles className="w-8 h-8 mr-4 text-yellow-400 animate-pulse" />
                <span className="bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400 bg-clip-text text-transparent">
                  Ferramentas de IA Profissionais
                </span>
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Remove Silence - Enhanced */}
                <div className="card-3d neumorphic-button p-8 rounded-2xl hover:bg-white/5 transition-all duration-500 group relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-pink-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center mb-6">
                      <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-pink-500 rounded-2xl flex items-center justify-center mr-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg shadow-red-500/25">
                        <Scissors className="w-8 h-8 text-white drop-shadow-lg" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">Remover Silêncios</h3>
                        <p className="text-sm text-red-400 font-medium">Auto-editor Avançado</p>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                      Remove automaticamente pausas, silêncios e detecta reinícios de fala após erros, criando transições cinematográficas suaves.
                    </p>
                    
                    <div className="space-y-3 mb-6 text-xs text-gray-400">
                      <div className="flex items-center">
                        <Zap className="w-3 h-3 mr-2 text-yellow-400" />
                        <span>Detecção inteligente de reinícios de fala</span>
                      </div>
                      <div className="flex items-center">
                        <Cpu className="w-3 h-3 mr-2 text-blue-400" />
                        <span>Remove hesitações e palavras de preenchimento</span>
                      </div>
                      <div className="flex items-center">
                        <Settings className="w-3 h-3 mr-2 text-purple-400" />
                        <span>Limite: {settings.silenceThreshold}dB | Margem: {settings.frameMargin} frames</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => startProcessing('remove_silence')}
                      disabled={isProcessing || !backendAvailable}
                      className="w-full modern-button bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed py-4 rounded-xl font-bold transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-red-500/25 hover:scale-105"
                    >
                      {isProcessing && activeOperation === 'remove_silence' ? (
                        <>
                          <Loader2 className="w-6 h-6 animate-spin" />
                          <span>Processando...</span>
                        </>
                      ) : (
                        <>
                          <Scissors className="w-6 h-6" />
                          <span>Processar Agora</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Remove Background - Enhanced */}
                <div className="card-3d neumorphic-button p-8 rounded-2xl hover:bg-white/5 transition-all duration-500 group relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center mb-6">
                      <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-2xl flex items-center justify-center mr-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg shadow-purple-500/25">
                        <Eraser className="w-8 h-8 text-white drop-shadow-lg" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">Remover Background</h3>
                        <p className="text-sm text-purple-400 font-medium">BiRefNet IA Premium</p>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                      Remoção de fundo ultra-rápida como CapCut, otimizada para velocidade máxima mantendo qualidade profissional.
                    </p>
                    
                    <div className="space-y-3 mb-6 text-xs text-gray-400">
                      <div className="flex items-center">
                        <Sparkles className="w-3 h-3 mr-2 text-purple-400" />
                        <span>Velocidade CapCut com qualidade profissional</span>
                      </div>
                      <div className="flex items-center">
                        <Monitor className="w-3 h-3 mr-2 text-blue-400" />
                        <span>Algoritmo otimizado para velocidade</span>
                      </div>
                      <div className="flex items-center">
                        <Settings className="w-3 h-3 mr-2 text-green-400" />
                        <span>Modo: {backgroundSettings.fastMode ? 'Rápido' : 'Alta Qualidade'} | {backgroundSettings.backgroundType}</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => startProcessing('remove_background')}
                      disabled={isProcessing || !backendAvailable}
                      className="w-full modern-button bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed py-4 rounded-xl font-bold transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-purple-500/25 hover:scale-105"
                    >
                      {isProcessing && activeOperation === 'remove_background' ? (
                        <>
                          <Loader2 className="w-6 h-6 animate-spin" />
                          <span>Processando...</span>
                        </>
                      ) : (
                        <>
                          <Eraser className="w-6 h-6" />
                          <span>Processar Agora</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Generate Subtitles - Enhanced */}
                <div className="card-3d neumorphic-button p-8 rounded-2xl hover:bg-white/5 transition-all duration-500 group relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-teal-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center mb-6">
                      <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-teal-500 rounded-2xl flex items-center justify-center mr-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg shadow-green-500/25">
                        <Subtitles className="w-8 h-8 text-white drop-shadow-lg" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">Gerar Legendas</h3>
                        <p className="text-sm text-green-400 font-medium">Whisper IA OpenAI</p>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                      Legendas sincronizadas com precisão milimétrica usando IA Whisper, exportáveis em formato SRT profissional.
                    </p>
                    
                    <div className="space-y-3 mb-6 text-xs text-gray-400">
                      <div className="flex items-center">
                        <HardDrive className="w-3 h-3 mr-2 text-green-400" />
                        <span>Sincronização perfeita</span>
                      </div>
                      <div className="flex items-center">
                        <FileVideo className="w-3 h-3 mr-2 text-blue-400" />
                        <span>Exportação SRT profissional</span>
                      </div>
                      <div className="flex items-center">
                        <Settings className="w-3 h-3 mr-2 text-yellow-400" />
                        <span>Idioma: {settings.subtitleLanguage}</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => startProcessing('generate_subtitles')}
                      disabled={isProcessing || !backendAvailable}
                      className="w-full modern-button bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed py-4 rounded-xl font-bold transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-green-500/25 hover:scale-105"
                    >
                      {isProcessing && activeOperation === 'generate_subtitles' ? (
                        <>
                          <Loader2 className="w-6 h-6 animate-spin" />
                          <span>Processando...</span>
                        </>
                      ) : (
                        <>
                          <Subtitles className="w-6 h-6" />
                          <span>Processar Agora</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Video Upscaler - New */}
                <div className="card-3d neumorphic-button p-8 rounded-2xl hover:bg-white/5 transition-all duration-500 group relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center mb-6">
                      <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mr-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg shadow-blue-500/25">
                        <Monitor className="w-8 h-8 text-white drop-shadow-lg" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">Upscale Vídeo</h3>
                        <p className="text-sm text-blue-400 font-medium">Video2X IA</p>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                      Aumenta a resolução do vídeo usando IA avançada, transformando 720p em 4K com qualidade cinematográfica.
                    </p>
                    
                    <div className="space-y-3 mb-6 text-xs text-gray-400">
                      <div className="flex items-center">
                        <Sparkles className="w-3 h-3 mr-2 text-blue-400" />
                        <span>Real-ESRGAN e Waifu2x</span>
                      </div>
                      <div className="flex items-center">
                        <Monitor className="w-3 h-3 mr-2 text-cyan-400" />
                        <span>2x e 4x upscaling</span>
                      </div>
                      <div className="flex items-center">
                        <Settings className="w-3 h-3 mr-2 text-green-400" />
                        <span>Preservação de detalhes</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => startProcessing('upscale_video')}
                      disabled={isProcessing || !backendAvailable}
                      className="w-full modern-button bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed py-4 rounded-xl font-bold transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-blue-500/25 hover:scale-105"
                    >
                      {isProcessing && activeOperation === 'upscale_video' ? (
                        <>
                          <Loader2 className="w-6 h-6 animate-spin" />
                          <span>Processando...</span>
                        </>
                      ) : (
                        <>
                          <Monitor className="w-6 h-6" />
                          <span>Upscale Agora</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Gaze Redirector - New */}
                <div className="card-3d neumorphic-button p-8 rounded-2xl hover:bg-white/5 transition-all duration-500 group relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-yellow-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="flex items-center mb-6">
                      <div className="w-16 h-16 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-2xl flex items-center justify-center mr-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500 shadow-lg shadow-orange-500/25">
                        <Sparkles className="w-8 h-8 text-white drop-shadow-lg" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">Redirecionar Olhar</h3>
                        <p className="text-sm text-orange-400 font-medium">Gaze Estimation IA</p>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                      Redireciona automaticamente o olhar para a câmera, criando conexão visual perfeita com o espectador.
                    </p>
                    
                    <div className="space-y-3 mb-6 text-xs text-gray-400">
                      <div className="flex items-center">
                        <Sparkles className="w-3 h-3 mr-2 text-orange-400" />
                        <span>Detecção facial avançada</span>
                      </div>
                      <div className="flex items-center">
                        <Monitor className="w-3 h-3 mr-2 text-yellow-400" />
                        <span>Rastreamento de olhos</span>
                      </div>
                      <div className="flex items-center">
                        <Settings className="w-3 h-3 mr-2 text-red-400" />
                        <span>Redirecionamento natural</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => startProcessing('redirect_gaze')}
                      disabled={isProcessing || !backendAvailable}
                      className="w-full modern-button bg-gradient-to-r from-orange-600 to-yellow-600 hover:from-orange-700 hover:to-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed py-4 rounded-xl font-bold transition-all duration-300 flex items-center justify-center space-x-3 shadow-lg hover:shadow-orange-500/25 hover:scale-105"
                    >
                      {isProcessing && activeOperation === 'redirect_gaze' ? (
                        <>
                          <Loader2 className="w-6 h-6 animate-spin" />
                          <span>Processando...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-6 h-6" />
                          <span>Redirecionar</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Background Removal Settings */}
        {originalVideo && (
          <div className="glass-morphism rounded-3xl p-8 shadow-2xl border border-white/10">
            <BackgroundRemovalSettings
              settings={backgroundSettings}
              onSettingsChange={setBackgroundSettings}
            />
          </div>
        )}

        {/* Enhanced Video Info */}
        {originalVideo && (
          <div className="glass-morphism rounded-3xl p-8 shadow-2xl border border-white/10 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-purple-600/5 to-pink-600/5"></div>
            
            <div className="relative z-10">
              <h3 className="text-2xl font-bold mb-6 flex items-center">
                <FileVideo className="w-6 h-6 mr-3 text-blue-400" />
                <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Informações do Projeto
                </span>
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="bg-gray-800/30 rounded-2xl p-6 border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300 group">
                  <div className="text-gray-400 mb-2 text-sm font-medium">Duração</div>
                  <div className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors duration-300">
                    {Math.floor(originalVideo.duration / 60)}:{Math.floor(originalVideo.duration % 60).toString().padStart(2, '0')}
                  </div>
                </div>
                
                <div className="bg-gray-800/30 rounded-2xl p-6 border border-gray-700/50 hover:border-purple-500/50 transition-all duration-300 group">
                  <div className="text-gray-400 mb-2 text-sm font-medium">Tamanho</div>
                  <div className="text-2xl font-bold text-white group-hover:text-purple-400 transition-colors duration-300">
                    {(originalVideo.size / (1024 * 1024)).toFixed(1)} MB
                  </div>
                </div>
                
                <div className="bg-gray-800/30 rounded-2xl p-6 border border-gray-700/50 hover:border-green-500/50 transition-all duration-300 group">
                  <div className="text-gray-400 mb-2 text-sm font-medium">Formato</div>
                  <div className="text-2xl font-bold text-white group-hover:text-green-400 transition-colors duration-300">
                    {originalVideo.format.split('/')[1]?.toUpperCase() || 'VIDEO'}
                  </div>
                </div>
                
                <div className="bg-gray-800/30 rounded-2xl p-6 border border-gray-700/50 hover:border-yellow-500/50 transition-all duration-300 group">
                  <div className="text-gray-400 mb-2 text-sm font-medium">Status</div>
                  <div className="text-lg font-bold flex items-center">
                    {processedVideo ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
                        <span className="text-green-400">Processado</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5 text-yellow-400 mr-2" />
                        <span className="text-yellow-400">Original</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Processing Modal */}
      {isProcessing && (
        <ProcessingModal
          status={processingStatus}
          onCancel={() => {
            setIsProcessing(false);
            setActiveOperation(null);
          }}
        />
      )}

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal
          settings={settings}
          onSettingsChange={setSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

export default App;