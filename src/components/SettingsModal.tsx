import React from 'react';
import { X, Settings, Save, RotateCcw } from 'lucide-react';
import { ProcessingSettings } from '../types';

interface SettingsModalProps {
  settings: ProcessingSettings;
  onSettingsChange: (settings: ProcessingSettings) => void;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ 
  settings, 
  onSettingsChange, 
  onClose 
}) => {
  const defaultSettings: ProcessingSettings = {
    silenceThreshold: -30,
    frameMargin: 6,
    videoQuality: 23,
    resolution: 'original',
    videoCodec: 'h264',
    exportFormat: 'mp4',
    enableSubtitles: true,
    subtitleLanguage: 'pt-BR'
  };

  const resetToDefaults = () => {
    onSettingsChange(defaultSettings);
  };

  const updateSetting = <K extends keyof ProcessingSettings>(
    key: K,
    value: ProcessingSettings[K]
  ) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden shadow-2xl border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <Settings className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">
              Configurações Avançadas
            </h2>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Audio Processing */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2">
                Processamento de Áudio
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Limite de Silêncio: {settings.silenceThreshold} dB
                  </label>
                  <input
                    type="range"
                    min="-60"
                    max="-10"
                    value={settings.silenceThreshold}
                    onChange={(e) => updateSetting('silenceThreshold', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Mais sensível</span>
                    <span>Menos sensível</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Margem de Quadros: {settings.frameMargin} frames
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="30"
                    value={settings.frameMargin}
                    onChange={(e) => updateSetting('frameMargin', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Frames preservados antes/depois dos cortes
                  </p>
                </div>
              </div>
            </div>

            {/* Video Processing */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2">
                Processamento de Vídeo
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Qualidade (CRF): {settings.videoQuality}
                  </label>
                  <input
                    type="range"
                    min="18"
                    max="28"
                    value={settings.videoQuality}
                    onChange={(e) => updateSetting('videoQuality', parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Alta qualidade</span>
                    <span>Arquivo menor</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Resolução de Saída
                  </label>
                  <select
                    value={settings.resolution}
                    onChange={(e) => updateSetting('resolution', e.target.value as any)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="original">Manter Original</option>
                    <option value="4k">4K (3840×2160)</option>
                    <option value="1080p">Full HD (1920×1080)</option>
                    <option value="720p">HD (1280×720)</option>
                    <option value="480p">SD (854×480)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Codec de Vídeo
                  </label>
                  <select
                    value={settings.videoCodec}
                    onChange={(e) => updateSetting('videoCodec', e.target.value as any)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="h264">H.264 (Máxima compatibilidade)</option>
                    <option value="h265">H.265 (Menor tamanho, mais lento)</option>
                    <option value="vp9">VP9 (Otimizado para web)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Export Settings */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2">
                Configurações de Exportação
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Formato de Saída
                  </label>
                  <select
                    value={settings.exportFormat}
                    onChange={(e) => updateSetting('exportFormat', e.target.value as any)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="mp4">MP4 (Recomendado)</option>
                    <option value="mov">MOV (Apple/Final Cut)</option>
                    <option value="avi">AVI (Compatibilidade)</option>
                    <option value="mkv">MKV (Código aberto)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Subtitle Settings */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2">
                Configurações de Legendas
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="enableSubtitlesModal"
                    checked={settings.enableSubtitles}
                    onChange={(e) => updateSetting('enableSubtitles', e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="enableSubtitlesModal" className="text-sm text-gray-300">
                    Gerar legendas automaticamente
                  </label>
                </div>

                {settings.enableSubtitles && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Idioma das Legendas
                    </label>
                    <select
                      value={settings.subtitleLanguage}
                      onChange={(e) => updateSetting('subtitleLanguage', e.target.value)}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pt-BR">Português (Brasil)</option>
                      <option value="en-US">English (United States)</option>
                      <option value="es-ES">Español (España)</option>
                      <option value="fr-FR">Français (France)</option>
                      <option value="de-DE">Deutsch (Deutschland)</option>
                      <option value="it-IT">Italiano (Italia)</option>
                      <option value="ja-JP">日本語 (Japan)</option>
                      <option value="ko-KR">한국어 (Korea)</option>
                    </select>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Performance Tips */}
          <div className="mt-8 p-4 bg-gray-900 rounded-lg">
            <h4 className="text-sm font-semibold text-yellow-400 mb-2">⚡ Dicas de Performance</h4>
            <ul className="text-xs text-gray-400 space-y-1">
              <li>• Use H.264 para máxima compatibilidade</li>
              <li>• CRF 23 oferece boa qualidade/tamanho</li>
              <li>• Resolução menor = processamento mais rápido</li>
              <li>• H.265 reduz tamanho mas demora mais para processar</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-700">
          <button
            onClick={resetToDefaults}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Restaurar Padrões</span>
          </button>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm"
            >
              Cancelar
            </button>
            <button
              onClick={onClose}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm"
            >
              <Save className="w-4 h-4" />
              <span>Salvar</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;