export interface ProcessingSettings {
  silenceThreshold: number;
  frameMargin: number;
  videoQuality: number;
  resolution: 'original' | '4k' | '1080p' | '720p' | '480p';
  videoCodec: 'h264' | 'h265' | 'vp9';
  exportFormat: 'mp4' | 'mov' | 'avi' | 'mkv';
  enableSubtitles: boolean;
  subtitleLanguage: string;
}

export interface ProcessingStatus {
  stage: 'idle' | 'analyzing' | 'processing' | 'encoding' | 'completed' | 'error';
  progress: number;
  message: string;
}

export interface VideoFile {
  file: File;
  url: string;
  duration: number;
  size: number;
  format: string;
}