import React from 'react';
import { X, Loader2, CheckCircle, AlertCircle, Volume2, Eraser, Subtitles, Film } from 'lucide-react';
import { ProcessingStatus } from '../types';

interface ProcessingModalProps {
  status: ProcessingStatus;
  onCancel: () => void;
}

const ProcessingModal: React.FC<ProcessingModalProps> = ({ status, onCancel }) => {
  const getStageIcon = () => {
    switch (status.stage) {
      case 'analyzing':
        return <Volume2 className="w-6 h-6 text-blue-400 animate-pulse" />;
      case 'processing':
        return <Eraser className="w-6 h-6 text-purple-400 animate-pulse" />;
      case 'encoding':
        return <Film className="w-6 h-6 text-green-400 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-6 h-6 text-red-400" />;
      default:
        return <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />;
    }
  };

  const getStageTitle = () => {
    switch (status.stage) {
      case 'analyzing':
        return 'Analisando Vídeo';
      case 'processing':
        return 'Processando';
      case 'encoding':
        return 'Codificando';
      case 'completed':
        return 'Concluído!';
      case 'error':
        return 'Erro';
      default:
        return 'Processando';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            {getStageIcon()}
            <h2 className="text-xl font-semibold text-white">
              {getStageTitle()}
            </h2>
          </div>
          
          {status.stage !== 'completed' && status.stage !== 'error' && (
            <button
              onClick={onCancel}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          )}
        </div>

        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">{status.message}</span>
              <span className="text-gray-400">{Math.round(status.progress)}%</span>
            </div>
            
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ease-out ${
                  status.stage === 'completed' 
                    ? 'bg-green-500' 
                    : status.stage === 'error'
                    ? 'bg-red-500'
                    : 'bg-gradient-to-r from-blue-500 to-purple-500'
                }`}
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>

          {/* Stage Indicators */}
          <div className="flex justify-between items-center pt-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                status.progress > 0 ? 'bg-blue-500' : 'bg-gray-600'
              }`} />
              <span className="text-xs text-gray-400">Análise</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                status.progress > 33 ? 'bg-purple-500' : 'bg-gray-600'
              }`} />
              <span className="text-xs text-gray-400">Processamento</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                status.progress > 66 ? 'bg-green-500' : 'bg-gray-600'
              }`} />
              <span className="text-xs text-gray-400">Codificação</span>
            </div>
          </div>

          {/* Action Buttons */}
          {status.stage === 'completed' && (
            <div className="pt-4">
              <button
                onClick={onCancel}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg transition-colors font-medium"
              >
                Continuar
              </button>
            </div>
          )}

          {status.stage === 'error' && (
            <div className="pt-4 space-y-2">
              <button
                onClick={onCancel}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg transition-colors font-medium"
              >
                Fechar
              </button>
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white py-2 rounded-lg transition-colors text-sm"
              >
                Tentar Novamente
              </button>
            </div>
          )}
        </div>

        {/* Processing Tips */}
        {status.stage !== 'completed' && status.stage !== 'error' && (
          <div className="mt-6 p-4 bg-gray-900 rounded-lg">
            <h4 className="text-sm font-medium text-gray-300 mb-2">💡 Dica:</h4>
            <p className="text-xs text-gray-400">
              {status.stage === 'analyzing' && 
                "Estamos analisando seu vídeo para identificar as melhores áreas para processamento."}
              {status.stage === 'processing' && 
                "Aplicando algoritmos avançados de IA para processar seu vídeo com máxima qualidade."}
              {status.stage === 'encoding' && 
                "Codificando o vídeo final com suas configurações personalizadas."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingModal;