import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, Server, Cpu, HardDrive, Activity } from 'lucide-react';

interface SystemStatusProps {
  backendAvailable: boolean;
  onRefresh: () => Promise<boolean>;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ backendAvailable, onRefresh }) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [systemInfo, setSystemInfo] = useState({
    cpu: 0,
    memory: 0,
    gpu: false
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
      // Simulate system info check
      setSystemInfo({
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        gpu: Math.random() > 0.5
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      if (backendAvailable) {
        setSystemInfo({
          cpu: Math.floor(Math.random() * 30) + 20,
          memory: Math.floor(Math.random() * 40) + 30,
          gpu: true
        });
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [backendAvailable]);

  return (
    <div className="flex items-center space-x-4">
      {/* Connection Status */}
      <div className={`flex items-center space-x-2 px-4 py-2 rounded-xl border transition-all duration-300 ${
        backendAvailable 
          ? 'bg-green-500/10 border-green-500/30 text-green-400' 
          : 'bg-red-500/10 border-red-500/30 text-red-400'
      }`}>
        {backendAvailable ? (
          <Wifi className="w-4 h-4" />
        ) : (
          <WifiOff className="w-4 h-4" />
        )}
        <span className="text-sm font-medium">
          {backendAvailable ? 'Online' : 'Offline'}
        </span>
      </div>

      {/* System Info */}
      {backendAvailable && (
        <div className="flex items-center space-x-3 text-xs text-gray-400">
          <div className="flex items-center space-x-1">
            <Cpu className="w-3 h-3" />
            <span>{systemInfo.cpu}%</span>
          </div>
          <div className="flex items-center space-x-1">
            <HardDrive className="w-3 h-3" />
            <span>{systemInfo.memory}%</span>
          </div>
          {systemInfo.gpu && (
            <div className="flex items-center space-x-1 text-green-400">
              <Activity className="w-3 h-3" />
              <span>GPU</span>
            </div>
          )}
        </div>
      )}

      {/* Refresh Button */}
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="neumorphic-button p-2 rounded-lg hover:bg-white/10 transition-all duration-300 disabled:opacity-50"
        title="Atualizar status do sistema"
      >
        <RefreshCw className={`w-4 h-4 text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
};

export default SystemStatus;