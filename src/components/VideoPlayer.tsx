import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, SkipBack, SkipForward, RotateCcw, Settings, Download } from 'lucide-react';

interface VideoPlayerProps {
  src: string | null;
  title: string;
  isOriginal: boolean;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ src, title, isOriginal }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => setCurrentTime(video.currentTime);
    const updateDuration = () => setDuration(video.duration);
    const handleEnded = () => setIsPlaying(false);
    const handleLoadStart = () => setIsLoading(true);
    const handleCanPlay = () => setIsLoading(false);

    video.addEventListener('timeupdate', updateTime);
    video.addEventListener('loadedmetadata', updateDuration);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('loadstart', handleLoadStart);
    video.addEventListener('canplay', handleCanPlay);

    return () => {
      video.removeEventListener('timeupdate', updateTime);
      video.removeEventListener('loadedmetadata', updateDuration);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('loadstart', handleLoadStart);
      video.removeEventListener('canplay', handleCanPlay);
    };
  }, [src]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;

    const time = parseFloat(e.target.value);
    video.currentTime = time;
    setCurrentTime(time);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;

    const newVolume = parseFloat(e.target.value);
    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isMuted) {
      video.volume = volume;
      setIsMuted(false);
    } else {
      video.volume = 0;
      setIsMuted(true);
    }
  };

  const skipTime = (seconds: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.currentTime = Math.max(0, Math.min(duration, video.currentTime + seconds));
  };

  const changePlaybackRate = (rate: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.playbackRate = rate;
    setPlaybackRate(rate);
  };

  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (!isFullscreen) {
      video.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!src) {
    return (
      <div className="glass-morphism rounded-3xl overflow-hidden shadow-2xl border border-white/10 transform hover:scale-[1.02] transition-all duration-300">
        <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 px-6 py-4 border-b border-white/10">
          <h3 className="font-semibold text-gray-200">{title}</h3>
        </div>
        <div className="aspect-video bg-gradient-to-br from-gray-900/50 to-gray-800/50 flex items-center justify-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-purple-600/5 to-pink-600/5"></div>
          <div className="text-center text-gray-400 relative z-10">
            <div className="w-20 h-20 glass-morphism rounded-3xl flex items-center justify-center mx-auto mb-4 shadow-2xl">
              <Play className="w-10 h-10 text-gray-500" />
            </div>
            <p className="text-lg font-medium">
              {isOriginal ? 'Carregue um vídeo para começar' : 'Aguardando processamento'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {isOriginal ? 'Arraste e solte ou clique para selecionar' : 'O vídeo processado aparecerá aqui'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-morphism rounded-3xl overflow-hidden shadow-2xl border border-white/10 transform hover:scale-[1.02] transition-all duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 px-6 py-4 border-b border-white/10 flex items-center justify-between">
        <h3 className="font-semibold text-gray-200 flex items-center">
          {title}
          {isLoading && (
            <div className="ml-3 w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          )}
        </h3>
        <div className="flex items-center space-x-3">
          {!isOriginal && (
            <span className="px-3 py-1 bg-gradient-to-r from-green-500 to-emerald-500 text-xs rounded-full text-white font-medium shadow-lg animate-pulse">
              ✨ Processado
            </span>
          )}
          
          {/* Playback Speed */}
          <div className="relative group">
            <button className="neumorphic-button p-2 hover:bg-white/10 rounded-lg transition-all duration-300">
              <span className="text-xs font-mono text-gray-300">{playbackRate}x</span>
            </button>
            <div className="absolute top-full right-0 mt-2 bg-gray-800 rounded-lg shadow-xl border border-gray-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10">
              {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
                <button
                  key={rate}
                  onClick={() => changePlaybackRate(rate)}
                  className={`block w-full px-4 py-2 text-sm text-left hover:bg-gray-700 transition-colors ${
                    playbackRate === rate ? 'text-blue-400' : 'text-gray-300'
                  }`}
                >
                  {rate}x
                </button>
              ))}
            </div>
          </div>
          
          <button 
            className="neumorphic-button p-2 hover:bg-white/10 rounded-lg transition-all duration-300"
            aria-label="Configurações do player"
          >
            <Settings className="w-4 h-4 text-gray-400 hover:text-white transition-colors duration-300" />
          </button>
        </div>
      </div>
      
      {/* Video Container */}
      <div 
        className="relative group"
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        <video
          ref={videoRef}
          src={src}
          className="w-full aspect-video bg-black"
          onClick={togglePlay}
          aria-label={`Player de vídeo - ${title}`}
        />
        
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
        
        {/* Video Controls Overlay */}
        <div className={`absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
          {/* Center Play Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={togglePlay}
              className="w-20 h-20 glass-morphism hover:bg-white/20 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110 shadow-2xl border border-white/20"
              aria-label={isPlaying ? 'Pausar vídeo' : 'Reproduzir vídeo'}
            >
              {isPlaying ? (
                <Pause className="w-10 h-10 text-white drop-shadow-lg" />
              ) : (
                <Play className="w-10 h-10 text-white ml-1 drop-shadow-lg" />
              )}
            </button>
          </div>

          {/* Bottom Controls */}
          <div className="absolute bottom-0 left-0 right-0 p-6">
            {/* Progress Bar */}
            <div className="mb-4">
              <label htmlFor={`progress-${isOriginal ? 'original' : 'processed'}`} className="sr-only">
                Progresso do vídeo
              </label>
              <div className="relative">
                <input
                  id={`progress-${isOriginal ? 'original' : 'processed'}`}
                  type="range"
                  min="0"
                  max={duration || 0}
                  value={currentTime}
                  onChange={handleSeek}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer modern-slider backdrop-blur-sm"
                  aria-label="Controle de progresso do vídeo"
                />
                {/* Progress indicator */}
                <div 
                  className="absolute top-0 left-0 h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg pointer-events-none"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={togglePlay}
                  className="neumorphic-button p-3 hover:bg-white/20 rounded-xl transition-all duration-300 shadow-lg"
                  aria-label={isPlaying ? 'Pausar' : 'Reproduzir'}
                >
                  {isPlaying ? (
                    <Pause className="w-6 h-6 text-white drop-shadow-lg" />
                  ) : (
                    <Play className="w-6 h-6 text-white drop-shadow-lg" />
                  )}
                </button>

                <button
                  onClick={() => skipTime(-10)}
                  className="neumorphic-button p-3 hover:bg-white/20 rounded-xl transition-all duration-300 shadow-lg"
                  aria-label="Voltar 10 segundos"
                >
                  <SkipBack className="w-6 h-6 text-white drop-shadow-lg" />
                </button>

                <button
                  onClick={() => skipTime(10)}
                  className="neumorphic-button p-3 hover:bg-white/20 rounded-xl transition-all duration-300 shadow-lg"
                  aria-label="Avançar 10 segundos"
                >
                  <SkipForward className="w-6 h-6 text-white drop-shadow-lg" />
                </button>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={toggleMute}
                    className="neumorphic-button p-3 hover:bg-white/20 rounded-xl transition-all duration-300 shadow-lg"
                    aria-label={isMuted ? 'Ativar som' : 'Silenciar'}
                  >
                    {isMuted ? (
                      <VolumeX className="w-6 h-6 text-white drop-shadow-lg" />
                    ) : (
                      <Volume2 className="w-6 h-6 text-white drop-shadow-lg" />
                    )}
                  </button>
                  <label htmlFor={`volume-${isOriginal ? 'original' : 'processed'}`} className="sr-only">
                    Controle de volume
                  </label>
                  <input
                    id={`volume-${isOriginal ? 'original' : 'processed'}`}
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={isMuted ? 0 : volume}
                    onChange={handleVolumeChange}
                    className="w-24 h-2 bg-white/20 rounded-lg appearance-none cursor-pointer modern-slider backdrop-blur-sm"
                    aria-label="Controle de volume"
                  />
                </div>

                <span className="text-white text-sm font-mono drop-shadow-lg bg-black/30 px-3 py-1 rounded-lg backdrop-blur-sm">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = 0;
                    }
                  }}
                  className="neumorphic-button p-3 hover:bg-white/20 rounded-xl transition-all duration-300 shadow-lg"
                  title="Reiniciar"
                  aria-label="Reiniciar vídeo"
                >
                  <RotateCcw className="w-6 h-6 text-white drop-shadow-lg" />
                </button>

                <button
                  onClick={toggleFullscreen}
                  className="neumorphic-button p-3 hover:bg-white/20 rounded-xl transition-all duration-300 shadow-lg"
                  aria-label="Tela cheia"
                >
                  <Maximize className="w-6 h-6 text-white drop-shadow-lg" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;