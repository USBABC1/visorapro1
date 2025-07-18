import React from 'react';
import { Eraser, Sparkles, Zap, Image as ImageIcon } from 'lucide-react';

interface BackgroundRemovalSettingsProps {
  settings: {
    fastMode: boolean;
    quality: 'low' | 'medium' | 'high';
    enhanceQuality: boolean;
    backgroundType: 'transparent' | 'color' | 'image';
    backgroundColor: string;
    backgroundImage: string | null;
  };
  onSettingsChange: (settings: any) => void;
}

const BackgroundRemovalSettings: React.FC<BackgroundRemovalSettingsProps> = ({
  settings,
  onSettingsChange
}) => {
  const updateSetting = (key: string, value: any) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
          <Eraser className="w-4 h-4 text-white" />
        </div>
        <h3 className="text-lg font-semibold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          Remoção de Background BiRefNet
        </h3>
      </div>

      {/* Processing Mode */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-300">
          Modo de Processamento
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => updateSetting('fastMode', false)}
            className={`p-4 rounded-xl border transition-all duration-300 ${
              !settings.fastMode
                ? 'bg-gradient-to-r from-purple-600/20 to-pink-600/20 border-purple-500/50 shadow-lg shadow-purple-500/25'
                : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="flex items-center space-x-3">
              <Sparkles className="w-5 h-5 text-purple-400" />
              <div className="text-left">
                <div className="font-medium text-white">Alta Qualidade</div>
                <div className="text-xs text-gray-400">BiRefNet completo</div>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => updateSetting('fastMode', true)}
            className={`p-4 rounded-xl border transition-all duration-300 ${
              settings.fastMode
                ? 'bg-gradient-to-r from-blue-600/20 to-cyan-600/20 border-blue-500/50 shadow-lg shadow-blue-500/25'
                : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="flex items-center space-x-3">
              <Zap className="w-5 h-5 text-blue-400" />
              <div className="text-left">
                <div className="font-medium text-white">Rápido</div>
                <div className="text-xs text-gray-400">BiRefNet Lite</div>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Quality Settings */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-300">
          Qualidade de Saída
        </label>
        <select
          value={settings.quality}
          onChange={(e) => updateSetting('quality', e.target.value)}
          className="w-full bg-gray-800/50 border border-gray-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-300"
        >
          <option value="high">Alta Qualidade (12Mbps)</option>
          <option value="medium">Qualidade Média (8Mbps)</option>
          <option value="low">Qualidade Baixa (4Mbps)</option>
        </select>
      </div>

      {/* Enhancement Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl border border-gray-700">
        <div>
          <div className="font-medium text-white">Aprimoramento de Qualidade</div>
          <div className="text-sm text-gray-400">
            Suavização de bordas e anti-aliasing
          </div>
        </div>
        <button
          onClick={() => updateSetting('enhanceQuality', !settings.enhanceQuality)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 ${
            settings.enhanceQuality ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-gray-600'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${
              settings.enhanceQuality ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {/* Background Type */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-300">
          Tipo de Background
        </label>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => updateSetting('backgroundType', 'transparent')}
            className={`p-3 rounded-xl border transition-all duration-300 ${
              settings.backgroundType === 'transparent'
                ? 'bg-gradient-to-r from-gray-600/20 to-gray-500/20 border-gray-400/50'
                : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="text-center">
              <div className="w-8 h-8 mx-auto mb-2 bg-gradient-to-br from-gray-400 to-gray-600 rounded-lg opacity-50"></div>
              <div className="text-xs text-gray-300">Transparente</div>
            </div>
          </button>
          
          <button
            onClick={() => updateSetting('backgroundType', 'color')}
            className={`p-3 rounded-xl border transition-all duration-300 ${
              settings.backgroundType === 'color'
                ? 'bg-gradient-to-r from-green-600/20 to-emerald-600/20 border-green-500/50'
                : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="text-center">
              <div 
                className="w-8 h-8 mx-auto mb-2 rounded-lg border border-gray-500"
                style={{ backgroundColor: settings.backgroundColor }}
              ></div>
              <div className="text-xs text-gray-300">Cor Sólida</div>
            </div>
          </button>
          
          <button
            onClick={() => updateSetting('backgroundType', 'image')}
            className={`p-3 rounded-xl border transition-all duration-300 ${
              settings.backgroundType === 'image'
                ? 'bg-gradient-to-r from-blue-600/20 to-cyan-600/20 border-blue-500/50'
                : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="text-center">
              <ImageIcon className="w-8 h-8 mx-auto mb-2 text-blue-400" />
              <div className="text-xs text-gray-300">Imagem</div>
            </div>
          </button>
        </div>
      </div>

      {/* Background Color Picker */}
      {settings.backgroundType === 'color' && (
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-300">
            Cor do Background
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="color"
              value={settings.backgroundColor}
              onChange={(e) => updateSetting('backgroundColor', e.target.value)}
              className="w-12 h-12 rounded-xl border border-gray-600 bg-transparent cursor-pointer"
            />
            <input
              type="text"
              value={settings.backgroundColor}
              onChange={(e) => updateSetting('backgroundColor', e.target.value)}
              className="flex-1 bg-gray-800/50 border border-gray-600 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="#00FF00"
            />
          </div>
        </div>
      )}

      {/* Background Image Upload */}
      {settings.backgroundType === 'image' && (
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-300">
            Imagem de Background
          </label>
          <div className="border-2 border-dashed border-gray-600 rounded-xl p-6 text-center hover:border-blue-500 transition-colors duration-300">
            <ImageIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-gray-400 mb-3">Arraste uma imagem ou clique para selecionar</p>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  const url = URL.createObjectURL(file);
                  updateSetting('backgroundImage', url);
                }
              }}
              className="hidden"
              id="background-image-upload"
            />
            <label
              htmlFor="background-image-upload"
              className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg cursor-pointer transition-colors duration-300"
            >
              Selecionar Imagem
            </label>
          </div>
          {settings.backgroundImage && (
            <div className="mt-3">
              <img
                src={settings.backgroundImage}
                alt="Background preview"
                className="w-full h-32 object-cover rounded-xl border border-gray-600"
              />
            </div>
          )}
        </div>
      )}

      {/* Quality Tips */}
      <div className="p-4 bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-xl border border-purple-500/20">
        <h4 className="text-sm font-semibold text-purple-300 mb-2 flex items-center">
          <Sparkles className="w-4 h-4 mr-2" />
          Dicas de Qualidade
        </h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• Use "Alta Qualidade" para resultados profissionais</li>
          <li>• "Aprimoramento" suaviza bordas e remove ruído</li>
          <li>• Backgrounds sólidos funcionam melhor que gradientes</li>
          <li>• Para vídeos longos, use "Modo Rápido" para economizar tempo</li>
        </ul>
      </div>
    </div>
  );
};

export default BackgroundRemovalSettings;