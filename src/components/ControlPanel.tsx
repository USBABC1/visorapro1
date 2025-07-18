import React from 'react';
import { Sliders, Volume2, Film, Monitor, FileVideo, Globe } from 'lucide-react';
import { ProcessingSettings } from '../types';

interface ControlPanelProps {
  settings: ProcessingSettings;
  onSettingsChange: (settings: ProcessingSettings) => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ settings, onSettingsChange }) => {
  const updateSetting = <K extends keyof ProcessingSettings>(
    key: K,
    value: ProcessingSettings[K]
  ) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  return (
    <div className="w-80 bg-gray-800 border-l border-gray-700 p-6 overflow-y-auto">
      <div className="flex items-center space-x-2 mb-6">
        <Sliders className="w-5 h-5 text-blue-400" />
        <h2 className="text-lg font-semibold">Configurações</h2>
      </div>

      <div className="space-y-6">
        {/* Audio Settings */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-3">
            <Volume2 className="w-4 h-4 text-purple-400" />
            <h3 className="font-medium text-gray-300">Configurações de Áudio</h3>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Limite de Silêncio (dB)
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="range"
                min="-60"
                max="-10"
                value={settings.silenceThreshold}
                onChange={(e) => updateSetting('silenceThreshold', parseInt(e.target.value))}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <span className="text-sm text-gray-300 w-12 text-right">
                {settings.silenceThreshold}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Sensibilidade para detecção de silêncios
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Margem de Quadros
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="range"
                min="1"
                max="30"
                value={settings.frameMargin}
                onChange={(e) => updateSetting('frameMargin', parseInt(e.target.value))}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <span className="text-sm text-gray-300 w-12 text-right">
                {settings.frameMargin}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Frames a manter antes/depois dos cortes
            </p>
          </div>
        </div>

        {/* Video Settings */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-3">
            <Film className="w-4 h-4 text-green-400" />
            <h3 className="font-medium text-gray-300">Configurações de Vídeo</h3>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Qualidade do Vídeo (CRF)
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="range"
                min="18"
                max="28"
                value={settings.videoQuality}
                onChange={(e) => updateSetting('videoQuality', parseInt(e.target.value))}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <span className="text-sm text-gray-300 w-12 text-right">
                {settings.videoQuality}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Menor valor = maior qualidade (18-28)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              <Monitor className="w-4 h-4 inline mr-1" />
              Resolução
            </label>
            <select
              value={settings.resolution}
              onChange={(e) => updateSetting('resolution', e.target.value as any)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="original">Original</option>
              <option value="4k">4K (3840x2160)</option>
              <option value="1080p">Full HD (1920x1080)</option>
              <option value="720p">HD (1280x720)</option>
              <option value="480p">SD (854x480)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              <FileVideo className="w-4 h-4 inline mr-1" />
              Codec de Vídeo
            </label>
            <select
              value={settings.videoCodec}
              onChange={(e) => updateSetting('videoCodec', e.target.value as any)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="h264">H.264 (Compatível)</option>
              <option value="h265">H.265 (Menor tamanho)</option>
              <option value="vp9">VP9 (Web otimizado)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Formato de Exportação
            </label>
            <select
              value={settings.exportFormat}
              onChange={(e) => updateSetting('exportFormat', e.target.value as any)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="mp4">MP4</option>
              <option value="mov">MOV</option>
              <option value="avi">AVI</option>
              <option value="mkv">MKV</option>
            </select>
          </div>
        </div>

        {/* Subtitle Settings */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-3">
            <Globe className="w-4 h-4 text-yellow-400" />
            <h3 className="font-medium text-gray-300">Configurações de Legendas</h3>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="enableSubtitles"
              checked={settings.enableSubtitles}
              onChange={(e) => updateSetting('enableSubtitles', e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="enableSubtitles" className="text-sm text-gray-300">
              Gerar legendas automaticamente
            </label>
          </div>

          {settings.enableSubtitles && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Idioma das Legendas
              </label>
              <select
                value={settings.subtitleLanguage}
                onChange={(e) => updateSetting('subtitleLanguage', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="pt-BR">Português (Brasil)</option>
                <option value="en-US">English (US)</option>
                <option value="es-ES">Español</option>
                <option value="fr-FR">Français</option>
                <option value="de-DE">Deutsch</option>
              </select>
            </div>
          )}
        </div>

        {/* Quick Presets */}
        <div className="space-y-4 pt-4 border-t border-gray-700">
          <h3 className="font-medium text-gray-300 mb-3">Presets Rápidos</h3>
          
          <div className="grid grid-cols-1 gap-2">
            <button
              onClick={() => onSettingsChange({
                ...settings,
                silenceThreshold: -25,
                frameMargin: 6,
                videoQuality: 20,
                resolution: '1080p',
                videoCodec: 'h264'
              })}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
            >
              🎥 YouTube/Social
            </button>
            
            <button
              onClick={() => onSettingsChange({
                ...settings,
                silenceThreshold: -30,
                frameMargin: 12,
                videoQuality: 18,
                resolution: 'original',
                videoCodec: 'h265'
              })}
              className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm transition-colors"
            >
              🎬 Alta Qualidade
            </button>
            
            <button
              onClick={() => onSettingsChange({
                ...settings,
                silenceThreshold: -20,
                frameMargin: 3,
                videoQuality: 25,
                resolution: '720p',
                videoCodec: 'h264'
              })}
              className="px-3 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm transition-colors"
            >
              ⚡ Rápido/Compacto
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;