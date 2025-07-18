import os
import random
import sys
import json
import wave
import subprocess
import concurrent.futures
import threading
from datetime import datetime
from pathlib import Path

import cv2
import ffmpeg
import numpy as np
from vosk import Model, KaldiRecognizer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
    QVBoxLayout, QHBoxLayout, QFrame, QMenuBar, QMenu,
    QStatusBar, QFileDialog, QProgressBar, QToolBar,
    QStyle, QSizePolicy, QScrollArea, QDoubleSpinBox, QSpinBox,
    QSlider, QComboBox, QLineEdit, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer, QUrl, QDir
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap, QPalette, QColor, QFont, QLinearGradient, QBrush
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import split_on_silence


class VideoProcessor:
    def __init__(self):
        self.report = {
            "video_original": "",
            "tempo_cortes": 45,
            "total_segmentos": 0,
            "segmentos": [],
            "transcricoes": [],
            "highlights": [],
            "video_compilado": "",
            "logs": []
        }
        self.vosk_model = None

    def initialize_vosk(self):
        """Initialize Vosk model only when needed"""
        if self.vosk_model is None:
            print("Carregando modelo Vosk...")
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model-pt")
            if os.path.exists(model_path):
                self.vosk_model = Model(model_path)  # Modelo para o idioma português
            else:
                self.report["logs"].append(f"Modelo Vosk não encontrado em {model_path}")
                raise Exception(f"Modelo Vosk não encontrado em {model_path}")

    def save_log(self, output_folder):
        """Save detailed processing logs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = Path(output_folder) / "process_log.txt"
        
        with open(log_file, "w", encoding="utf-8") as log:
            log.write(f"Processamento Iniciado: {timestamp}\n")
            for entry in self.report["logs"]:
                log.write(f"{entry}\n")
            
        self.report["logs"].append(f"Log salvo em {log_file}")
        return log_file

    def extract_audio(self, video_path, output_folder):
        """Extract audio from video for transcription"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            audio_path = Path(output_folder) / "audio.wav"
            
            (ffmpeg
                .input(str(video_path))
                .output(str(audio_path), acodec="pcm_s16le", ac=1, ar="16000")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            self.report["logs"].append(f"Áudio extraído com sucesso: {audio_path}")
            return str(audio_path)
            
        except ffmpeg.Error as e:
            self.report["logs"].append(f"Erro ao extrair áudio: {e.stderr.decode()}")
            return None

    def generate_transcript(self, audio_path):
        """Generate transcript using Vosk AI"""
        try:
            self.initialize_vosk()
            recognizer = KaldiRecognizer(self.vosk_model, 16000)
            # Habilitar timestamps para cada palavra
            recognizer.SetWords(True)

            # Ler o áudio
            with wave.open(audio_path, "rb") as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                    raise ValueError("O áudio deve ser mono, 16-bit PCM e 16kHz.")

                transcript = ""
                word_results = []
                
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        transcript += result.get("text", "") + " "
                        if "result" in result:
                            word_results.extend(result["result"])
                
                # Processar a última parte do áudio
                final_result = json.loads(recognizer.FinalResult())
                transcript += final_result.get("text", "")
                if "result" in final_result:
                    word_results.extend(final_result["result"])

            self.report["logs"].append(f"Transcrição gerada: {len(transcript.split())} palavras")
            return {"text": transcript.strip(), "words": word_results}
        except Exception as e:
            self.report["logs"].append(f"Erro na transcrição: {str(e)}")
            return {"text": "", "words": []}

    def segment_video(self, filename, output_folder, segment_time):
        """Segment video into smaller clips"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            output_pattern = str(Path(output_folder) / "segment%d.mp4")
            
            (ffmpeg
                .input(filename)
                .output(output_pattern, f='segment', segment_time=segment_time, reset_timestamps=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            segment_files = sorted([f for f in os.listdir(output_folder) if f.startswith("segment") and f.endswith(".mp4")])
            self.report["segmentos"] = [str(Path(output_folder) / f) for f in segment_files]
            self.report["total_segmentos"] = len(segment_files)
            self.report["logs"].append(f"Vídeo segmentado em {len(segment_files)} partes")
            
        except ffmpeg.Error as e:
            self.report["logs"].append(f"Erro ao segmentar vídeo: {e.stderr.decode()}")

    def _format_srt_time(self, seconds):
        """Formata segundos para o formato de tempo SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds_remainder):02d},{milliseconds:03d}"

    def generate_srt(self, transcript_data, output_path, filename):
        """Generate SRT subtitle file with proper synchronization"""
        try:
            srt_file = Path(output_path) / f"{filename}.srt"
            
            # Se não temos palavras com timestamps, usamos uma estimativa simples
            if not transcript_data.get("words"):
                with open(srt_file, "w", encoding="utf-8") as f:
                    start_time = "00:00:00,000"
                    # Estimativa de 2 segundos por palavra para o texto completo
                    word_count = len(transcript_data["text"].split())
                    duration_seconds = word_count * 2
                    end_time = self._format_srt_time(duration_seconds)
                    
                    f.write("1\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{transcript_data['text'].strip()}\n\n")
                
                self.report["logs"].append(f"Legendas estimadas geradas em {srt_file}")
                return str(srt_file)
            
            # Agrupar palavras em frases (8-10 palavras por legenda)
            words = transcript_data["words"]
            if not words:
                self.report["logs"].append("Sem palavras para gerar legendas.")
                return None
                
            phrases = []
            current_phrase = []
            current_start = words[0]["start"]
            
            for word in words:
                current_phrase.append(word)
                
                # Criar nova frase após 8-10 palavras ou quando encontramos pontuação
                if len(current_phrase) >= 8 and (
                    word["word"].endswith('.') or 
                    word["word"].endswith('!') or 
                    word["word"].endswith('?') or 
                    word["word"].endswith(',')
                ):
                    phrases.append({
                        "start": current_start,
                        "end": word["end"],
                        "text": " ".join(w["word"] for w in current_phrase)
                    })
                    if len(words) > words.index(word) + 1:
                        current_start = words[words.index(word) + 1]["start"]
                    current_phrase = []
                elif len(current_phrase) >= 10:
                    phrases.append({
                        "start": current_start,
                        "end": word["end"],
                        "text": " ".join(w["word"] for w in current_phrase)
                    })
                    if len(words) > words.index(word) + 1:
                        current_start = words[words.index(word) + 1]["start"]
                    current_phrase = []
            
            # Adicionar a última frase se existir
            if current_phrase:
                phrases.append({
                    "start": current_start,
                    "end": current_phrase[-1]["end"],
                    "text": " ".join(w["word"] for w in current_phrase)
                })
                
            # Gerar arquivo SRT
            with open(srt_file, "w", encoding="utf-8") as f:
                for i, phrase in enumerate(phrases, 1):
                    start_time = self._format_srt_time(phrase["start"])
                    end_time = self._format_srt_time(phrase["end"])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{phrase['text']}\n\n")
                    
            self.report["logs"].append(f"Legendas sincronizadas geradas em {srt_file}")
            return str(srt_file)
            
        except Exception as e:
            self.report["logs"].append(f"Erro ao gerar legendas: {str(e)}")
            return None

    def score_highlight(self, transcript):
        """Score segment for highlight detection"""
        keywords = ["importante", "atenção", "urgente", "notícia", "destaque"]
        score = sum(transcript.lower().count(word) * 10 for word in keywords)
        return score

    def save_highlight_clip(self, segment_path, transcript_data, output_folder):
        """Save highlight video clip and generate subtitles"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            
            # Gerar nome baseado no tema principal
            words = transcript_data["text"].split()[:5]
            theme_name = "_".join(words) if words else f"highlight_{os.path.basename(segment_path)}"
            clip_name = f"{theme_name}.mp4"
            output_file = Path(output_folder) / clip_name
            
            # Salvar o clipe
            (ffmpeg
                .input(str(segment_path))
                .output(str(output_file))
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            self.report["logs"].append(f"Highlight salvo: {output_file}")
            self.report["highlights"].append(str(output_file))
            
            # Gerar legenda para o clipe
            self.generate_srt(transcript_data, output_folder, theme_name)
            
            return str(output_file)
            
        except ffmpeg.Error as e:
            self.report["logs"].append(f"Erro ao salvar highlight: {e.stderr.decode()}")
            return None

    def merge_highlights(self, highlight_clips, output_folder, theme_name="video_compilado"):
        """Merge highlight clips into final video"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            output_file = Path(output_folder) / f"{theme_name}.mp4"
            
            if not highlight_clips:
                self.report["logs"].append("Nenhum highlight para compilar")
                return None
                
            if len(highlight_clips) == 1:
                os.rename(highlight_clips[0], str(output_file))
            else:
                # Criar lista de arquivos para concatenação
                concat_file = Path(output_folder) / "concat_list.txt"
                with open(concat_file, "w") as f:
                    for clip in highlight_clips:
                        f.write(f"file '{os.path.abspath(clip)}'\n")
                
                # Executar concatenação
                subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                    "-i", str(concat_file), "-c", "copy", str(output_file)
                ], check=True)
            
            self.report["logs"].append(f"Highlights compilados em {output_file}")
            self.report["video_compilado"] = str(output_file)
            return str(output_file)
            
        except Exception as e:
            self.report["logs"].append(f"Erro ao compilar highlights: {str(e)}")
            return None

    def convert_to_story(self, video_path, output_folder):
        """Convert video to vertical format (1080x1920) for Instagram/TikTok stories"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            output_file = Path(output_folder) / f"story_{Path(video_path).stem}.mp4"
            
            # Get video information
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            width = int(video_info['width'])
            height = int(video_info['height'])
            
            # Determine the scale and crop for vertical format
            # We'll center the content and scale to fit 1080x1920
            scale_factor = 1920 / height
            new_width = int(width * scale_factor)
            crop_x = (new_width - 1080) // 2
            
            # Apply transformations
            (ffmpeg
                .input(video_path)
                .filter('scale', new_width, 1920)
                .filter('crop', 1080, 1920, crop_x, 0)
                .output(str(output_file))
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            self.report["logs"].append(f"Vídeo convertido para formato Story: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.report["logs"].append(f"Erro ao converter para formato Story: {str(e)}")
            return None

    def convert_to_feed(self, video_path, output_folder):
        """Convert video to square format (1080x1080) for Instagram feed"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            output_file = Path(output_folder) / f"feed_{Path(video_path).stem}.mp4"
            
            # Get video information
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            width = int(video_info['width'])
            height = int(video_info['height'])
            
            # Calculate scaling parameters
            if width > height:
                scale_h = 1080
                scale_w = -1
                pad_w = 0
                pad_h = (1080 - int(height * 1080 / width)) // 2
            else:
                scale_w = 1080
                scale_h = -1
                pad_h = 0
                pad_w = (1080 - int(width * 1080 / height)) // 2
            
            # Apply transformations: scale and center with black padding
            (ffmpeg
                .input(video_path)
                .filter('scale', scale_w, scale_h)
                .filter('pad', 1080, 1080, pad_w, pad_h, color='black')
                .output(str(output_file))
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            self.report["logs"].append(f"Vídeo convertido para formato Feed: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.report["logs"].append(f"Erro ao converter para formato Feed: {str(e)}")
            return None

    def remove_silence(self, video_path, output_folder, silence_threshold=-40, min_silence_len=1000):
        """Remove silence from video for automatic editing"""
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
            output_file = Path(output_folder) / f"sem_silencio_{Path(video_path).stem}.mp4"
            
            # Extract audio for silence detection
            temp_audio = Path(output_folder) / "temp_audio.wav"
            (ffmpeg
                .input(video_path)
                .output(str(temp_audio), acodec="pcm_s16le", ac=1, ar="44100")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            # Detect non-silent segments
            audio = AudioSegment.from_wav(str(temp_audio))
            non_silent_chunks = split_on_silence(
                audio, 
                min_silence_len=min_silence_len,
                silence_thresh=silence_threshold,
                keep_silence=300  # Keep 300ms of silence at segment boundaries
            )
            
            # Create list of timestamps for non-silent segments
            segments = []
            start_time = 0
            for chunk in non_silent_chunks:
                end_time = start_time + len(chunk) / 1000.0  # ms to seconds
                segments.append((start_time, end_time))
                start_time = end_time
            
            # Create temporary file with segments
            segments_file = Path(output_folder) / "segments.txt"
            with open(segments_file, "w") as f:
                for i, (start, end) in enumerate(segments):
                    segment_file = Path(output_folder) / f"temp_segment_{i}.mp4"
                    duration = end - start
                    
                    # Extract segment from original video
                    (ffmpeg
                        .input(video_path, ss=start, t=duration)
                        .output(str(segment_file), c="copy")
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True))
                    
                    f.write(f"file '{segment_file.absolute()}'\n")
            
            # Concatenate segments
            (ffmpeg
                .input(str(segments_file), format="concat", safe=0)
                .output(str(output_file), c="copy")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            # Cleanup temporary files
            for i in range(len(segments)):
                segment_file = Path(output_folder) / f"temp_segment_{i}.mp4"
                if segment_file.exists():
                    os.remove(segment_file)
            if Path(temp_audio).exists():
                os.remove(temp_audio)
            if Path(segments_file).exists():
                os.remove(segments_file)
            
            self.report["logs"].append(f"Vídeo sem silêncio salvo em: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.report["logs"].append(f"Erro ao remover silêncio: {str(e)}")
            return None


class ProcessingThread(QThread):
    update_progress = pyqtSignal(int, str)
    processing_complete = pyqtSignal(bool, str)
    update_highlights = pyqtSignal(list)
    
    def __init__(self, processor, video_path, corte_time):
        super().__init__()
        self.processor = processor
        self.video_path = video_path
        self.corte_time = corte_time
        self.highlight_clips = []
        
    def run(self):
        try:
            base_dir = Path("Visoria_Output")
            base_dir.mkdir(parents=True, exist_ok=True)
            output_folder = base_dir / f"Processo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_folder.mkdir(parents=True, exist_ok=True)
            
            self.processor.report["video_original"] = self.video_path
            self.processor.report["tempo_cortes"] = self.corte_time
            
            # Extract audio
            self.update_progress.emit(10, "Extraindo áudio...")
            audio_path = self.processor.extract_audio(
                self.video_path, 
                output_folder / "audio"
            )
            if not audio_path:
                self.processing_complete.emit(False, "Erro ao extrair áudio do vídeo.")
                return
                
            # Generate transcript for the full video
            self.update_progress.emit(20, "Gerando transcrição completa...")
            transcript_data = self.processor.generate_transcript(audio_path)
            self.processor.report["transcricoes"].append(transcript_data["text"])
            
            # Generate SRT for the full video
            self.update_progress.emit(30, "Gerando legendas...")
            self.processor.generate_srt(transcript_data, output_folder, "legenda_completa")
            
            # Segment video
            self.update_progress.emit(40, "Segmentando vídeo...")
            self.processor.segment_video(
                self.video_path, 
                output_folder / "segmentos",
                self.processor.report["tempo_cortes"]
            )
            
            # Process segments for highlights
            self.update_progress.emit(50, "Identificando highlights...")
            highlight_clips = []
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for i, segment in enumerate(self.processor.report["segmentos"]):
                    self.update_progress.emit(
                        50 + int((i / len(self.processor.report["segmentos"])) * 30),
                        f"Processando segmento {i+1} de {len(self.processor.report['segmentos'])}..."
                    )
                    
                    # Extract audio from each segment
                    segment_audio_path = self.processor.extract_audio(
                        segment, 
                        output_folder / "segmentos_audio"
                    )
                    if not segment_audio_path:
                        continue
                        
                    # Generate transcript for the segment
                    segment_transcript_data = self.processor.generate_transcript(segment_audio_path)
                    
                    # Save highlight clip and generate subtitles
                    future = executor.submit(
                        self.processor.save_highlight_clip,
                        segment,
                        segment_transcript_data,
                        output_folder / "highlights"
                    )
                    futures.append(future)
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        highlight_clips.append(result)
                        # Atualizar a lista de highlights em tempo real
                        self.update_highlights.emit(self.processor.report["highlights"])
            
            # Merge highlights
            self.update_progress.emit(90, "Compilando highlights...")
            final_video = self.processor.merge_highlights(highlight_clips, output_folder)
            
            # Save log
            self.update_progress.emit(95, "Salvando logs...")
            log_file = self.processor.save_log(output_folder)
            
            self.update_progress.emit(100, "Processamento concluído!")
            self.processing_complete.emit(True, f"Processamento concluído com sucesso!\nLog: {log_file}")
            
        except Exception as e:
            self.processing_complete.emit(False, f"Erro durante o processamento: {str(e)}")


class NeomorphicButton(QPushButton):
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1e2127;
                color: #e1e1e1;
                border-radius: 10px;
                font-weight: bold;
                padding: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #282c34;
                color: #4fc3f7;
            }
            QPushButton:pressed {
                background-color: #1a1d22;
                border-top: 2px solid #1a1d22;
                border-left: 2px solid #1a1d22;
                border-bottom: 2px solid #2c313c;
                border-right: 2px solid #2c313c;
            }
        """)
        
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(32, 32))


class VideoThumbnail(QWidget):
    clicked = pyqtSignal(str)
    
    def __init__(self, video_path, title, duration, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Frame para o thumbnail com efeito neomórfico
        frame = QFrame()
        frame.setObjectName("thumbnailFrame")
        frame.setStyleSheet("""
            #thumbnailFrame {
                background-color: #1e2127;
                border-radius: 8px;
                border-top: 2px solid #2c313c;
                border-left: 2px solid #2c313c;
                border-bottom: 2px solid #1a1d22;
                border-right: 2px solid #1a1d22;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        
        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(180, 120)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setStyleSheet("background-color: #141414; border-radius: 5px;")
        
        # Gerar thumbnail do vídeo
        self.generate_thumbnail()
        
        # Título e duração
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e1e1e1; font-weight: bold;")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        duration_label = QLabel(duration)
        duration_label.setStyleSheet("color: #7f8c8d;")
        duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        frame_layout.addWidget(self.thumbnail)
        frame_layout.addWidget(title_label)
        frame_layout.addWidget(duration_label)
        
        layout.addWidget(frame)
        self.setLayout(layout)
        
    def generate_thumbnail(self):
        try:
            # Capturar o frame do vídeo para o thumbnail
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            if ret:
                # Converter para RGB e redimensionar
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (180, 120))
                
                # Converter para QImage e QPixmap
                h, w, ch = frame.shape
                image = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                self.thumbnail.setPixmap(pixmap)
            cap.release()
        except Exception as e:
            print(f"Erro ao gerar thumbnail: {e}")
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.video_path)
        super().mousePressEvent(event)


class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                background-color: #1a1d22;
                border-radius: 8px;
                border-top: 2px solid #1a1d22;
                border-left: 2px solid #1a1d22;
                border-bottom: 2px solid #2c313c;
                border-right: 2px solid #2c313c;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                stop:0 #0a84ff, stop:1 #4fc3f7);
                border-radius: 8px;
            }
        """)
        self.setMinimumHeight(20)
        self.setTextVisible(True)


class VisoriaProUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = VideoProcessor()
        self.processing_thread = None
        self.current_video = ""
        self.highlights = []
        
        self.setWindowTitle("VISORIA PRO V3")
        self.setMinimumSize(1600, 900)
        
        # Configurar estilo da aplicação
        self.setup_styles()
        
        # Configurar widgets e layout
        self.setup_ui()
        
    def setup_styles(self):
        # Definir a paleta de cores para tema escuro
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 33, 39))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(225, 225, 225))
        palette.setColor(QPalette.ColorRole.Base, QColor(26, 29, 34))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(44, 49, 60))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(225, 225, 225))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(225, 225, 225))
        palette.setColor(QPalette.ColorRole.Text, QColor(225, 225, 225))
        palette.setColor(QPalette.ColorRole.Button, QColor(30, 33, 39))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(225, 225, 225))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(79, 195, 247))
        palette.setColor(QPalette.ColorRole.Link, QColor(79, 195, 247))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(79, 195, 247))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(20, 20, 20))
        
        self.setPalette(palette)
        
        # Aplicar estilo CSS para tema neomórfico
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e2127;
                color: #e1e1e1;
            }
            QWidget {
                background-color: #1e2127;
                color: #e1e1e1;
            }
            QFrame {
                background-color: #1e2127;
                border: none;
            }
            QLabel {
                color: #e1e1e1;
            }
            QScrollArea {
                background-color: #1e2127;
                border: none;
            }
            QLineEdit {
                background-color: #1a1d22;
                color: #e1e1e1;
                border-radius: 8px;
                padding: 8px;
                border-top: 2px solid #1a1d22;
                border-left: 2px solid #1a1d22;
                border-bottom: 2px solid #2c313c;
                border-right: 2px solid #2c313c;
            }
            QComboBox {
                background-color: #1a1d22;
                color: #e1e1e1;
                border-radius: 8px;
                padding: 8px;
                border-top: 2px solid #1a1d22;
                border-left: 2px solid #1a1d22;
                border-bottom: 2px solid #2c313c;
                border-right: 2px solid #2c313c;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Sidebar esquerda com botões
        left_sidebar = self.create_left_sidebar()
        main_layout.addWidget(left_sidebar)
        
        # Área central
        center_area = self.create_center_area()
        main_layout.addWidget(center_area)
        
        # Sidebar direita com highlights
        right_sidebar = self.create_right_sidebar()
        main_layout.addWidget(right_sidebar)
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Barra de progresso
        self.progress_bar = CustomProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Label de status
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #4fc3f7; font-weight: bold;")
        self.status_bar.addWidget(self.status_label)
        
    def create_left_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(80)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1a1d22;
                border-radius: 15px;
                border-top: 2px solid #2c313c;
                border-left: 2px solid #2c313c;
                border-bottom: 2px solid #1a1d22;
                border-right: 2px solid #1a1d22;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Botões da sidebar
        buttons = [
            ("Abrir", "📁", self.open_file),
            ("Corte", "✂️", self.cut_video),
            ("Legenda", "💬", self.add_subtitles),
            ("Exportar", "📤", self.export_video),
            ("Baixar", "⬇️", self.download_video),
        ]
        
        for text, icon, callback in buttons:
            btn = NeomorphicButton(icon)
            btn.setToolTip(text)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        layout.addStretch()
        return sidebar
        
    def create_center_area(self):
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(10)
        
        # Área superior com player principal
        top_area = QWidget()
        top_layout = QHBoxLayout(top_area)
        
        # Player principal
        self.video_player = self.create_video_player()
        top_layout.addWidget(self.video_player)
        
        # Área de controles
        controls_area = self.create_controls_area()
        top_layout.addWidget(controls_area)
        
        center_layout.addWidget(top_area)
        
        # Área inferior com informações
        self.info_area = self.create_info_area()
        center_layout.addWidget(self.info_area)
        
        return center_widget
        
    def create_video_player(self):
        player_widget = QWidget()
        player_widget.setFixedSize(640, 360)  # Proporção 16:9
        player_widget.setStyleSheet("""
            QWidget {
                background-color: #000000;
                border-radius: 10px;
                border-top: 2px solid #2c313c;
                border-left: 2px solid #2c313c;
                border-bottom: 2px solid #1a1d22;
                border-right: 2px solid #1a1d22;
            }
        """)
        
        layout = QVBoxLayout(player_widget)
        
        # Placeholder para o player
        self.player_label = QLabel("Carregue um vídeo para começar")
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        layout.addWidget(self.player_label)
        
        return player_widget
        
    def create_controls_area(self):
        controls_widget = QWidget()
        controls_widget.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(10)
        
        # Botões principais
        main_buttons = [
            ("Processar Highlights", "🎬", self.process_highlights),
            ("Edição Automática", "🤖", self.auto_edit),
            ("Converter para Story", "📱", self.convert_to_story),
            ("Converter para Feed", "📊", self.convert_to_feed),
        ]
        
        for text, icon, callback in main_buttons:
            btn = QPushButton(f"{icon} {text}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a1d22;
                    color: #e1e1e1;
                    border-radius: 8px;
                    padding: 10px;
                    font-weight: bold;
                    border-top: 2px solid #2c313c;
                    border-left: 2px solid #2c313c;
                    border-bottom: 2px solid #1a1d22;
                    border-right: 2px solid #1a1d22;
                }
                QPushButton:hover {
                    background-color: #282c34;
                    color: #4fc3f7;
                }
                QPushButton:pressed {
                    background-color: #1a1d22;
                    border-top: 2px solid #1a1d22;
                    border-left: 2px solid #1a1d22;
                    border-bottom: 2px solid #2c313c;
                    border-right: 2px solid #2c313c;
                }
            """)
            btn.clicked.connect(callback)
            controls_layout.addWidget(btn)
        
        # Configurações
        settings_group = QGroupBox("Configurações")
        settings_group.setStyleSheet("""
            QGroupBox {
                color: #e1e1e1;
                font-weight: bold;
                border: 1px solid #2c313c;
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        settings_layout = QVBoxLayout(settings_group)
        
        # Tempo de corte
        cut_time_label = QLabel("Tempo de Corte (segundos):")
        cut_time_label.setStyleSheet("color: #e1e1e1;")
        self.cut_time_spin = QSpinBox()
        self.cut_time_spin.setRange(10, 300)
        self.cut_time_spin.setValue(45)
        self.cut_time_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1a1d22;
                color: #e1e1e1;
                border-radius: 5px;
                padding: 5px;
                border-top: 2px solid #1a1d22;
                border-left: 2px solid #1a1d22;
                border-bottom: 2px solid #2c313c;
                border-right: 2px solid #2c313c;
            }
        """)
        
        settings_layout.addWidget(cut_time_label)
        settings_layout.addWidget(self.cut_time_spin)
        
        controls_layout.addWidget(settings_group)
        controls_layout.addStretch()
        
        return controls_widget
        
    def create_info_area(self):
        info_widget = QWidget()
        info_widget.setFixedHeight(150)
        info_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1d22;
                border-radius: 10px;
                border-top: 2px solid #2c313c;
                border-left: 2px solid #2c313c;
                border-bottom: 2px solid #1a1d22;
                border-right: 2px solid #1a1d22;
            }
        """)
        
        layout = QVBoxLayout(info_widget)
        
        # Título
        title_label = QLabel("Informações do Projeto")
        title_label.setStyleSheet("color: #4fc3f7; font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Área de texto para logs
        self.log_text = QLabel("Nenhum projeto carregado")
        self.log_text.setStyleSheet("color: #e1e1e1; font-size: 12px;")
        self.log_text.setWordWrap(True)
        self.log_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.log_text)
        
        return info_widget
        
    def create_right_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1a1d22;
                border-radius: 15px;
                border-top: 2px solid #2c313c;
                border-left: 2px solid #2c313c;
                border-bottom: 2px solid #1a1d22;
                border-right: 2px solid #1a1d22;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        title_label = QLabel("HIGHLIGHTS")
        title_label.setStyleSheet("color: #4fc3f7; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Área de scroll para highlights
        self.highlights_scroll = QScrollArea()
        self.highlights_scroll.setWidgetResizable(True)
        self.highlights_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.highlights_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.highlights_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1d22;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #4fc3f7;
                border-radius: 5px;
            }
        """)
        
        self.highlights_widget = QWidget()
        self.highlights_layout = QVBoxLayout(self.highlights_widget)
        self.highlights_layout.setSpacing(10)
        self.highlights_layout.setContentsMargins(5, 5, 5, 5)
        
        # Placeholder
        placeholder = QLabel("Nenhum highlight processado")
        placeholder.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.highlights_layout.addWidget(placeholder)
        
        self.highlights_scroll.setWidget(self.highlights_widget)
        layout.addWidget(self.highlights_scroll)
        
        return sidebar
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Vídeo", 
            "", 
            "Vídeos (*.mp4 *.avi *.mkv *.mov *.wmv)"
        )
        
        if file_path:
            self.current_video = file_path
            self.player_label.setText(f"Vídeo carregado: {Path(file_path).name}")
            self.log_text.setText(f"Arquivo carregado: {Path(file_path).name}")
            self.status_label.setText("Vídeo carregado com sucesso")
            
    def cut_video(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
        self.status_label.setText("Função de corte será implementada")
        
    def add_subtitles(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
        self.status_label.setText("Função de legendas será implementada")
        
    def export_video(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
            
        # Diálogo de exportação
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Vídeo",
            "",
            "MP4 (*.mp4);;AVI (*.avi);;MKV (*.mkv);;MP3 (*.mp3);;WAV (*.wav)"
        )
        
        if file_path:
            self.status_label.setText(f"Exportando para: {file_path}")
            
    def download_video(self):
        # Diálogo para inserir URL
        from PyQt6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(self, "Baixar Vídeo", "URL do vídeo:")
        if ok and url:
            self.status_label.setText(f"Baixando: {url}")
            
    def process_highlights(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
            
        self.status_label.setText("Processando highlights...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Iniciar thread de processamento
        self.processing_thread = ProcessingThread(
            self.processor, 
            self.current_video, 
            self.cut_time_spin.value()
        )
        self.processing_thread.update_progress.connect(self.update_progress)
        self.processing_thread.processing_complete.connect(self.processing_complete)
        self.processing_thread.update_highlights.connect(self.update_highlights)
        self.processing_thread.start()
        
    def auto_edit(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
            
        self.status_label.setText("Iniciando edição automática...")
        
        # Executar remoção de silêncio em thread separada
        def run_auto_edit():
            try:
                output_folder = Path("Visoria_Output") / "Edicao_Automatica"
                result = self.processor.remove_silence(self.current_video, output_folder)
                if result:
                    self.status_label.setText(f"Edição automática concluída: {result}")
                else:
                    self.status_label.setText("Erro na edição automática")
            except Exception as e:
                self.status_label.setText(f"Erro: {str(e)}")
        
        threading.Thread(target=run_auto_edit, daemon=True).start()
        
    def convert_to_story(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
            
        self.status_label.setText("Convertendo para formato Story...")
        
        def run_story_conversion():
            try:
                output_folder = Path("Visoria_Output") / "Story_Format"
                result = self.processor.convert_to_story(self.current_video, output_folder)
                if result:
                    self.status_label.setText(f"Conversão para Story concluída: {result}")
                else:
                    self.status_label.setText("Erro na conversão para Story")
            except Exception as e:
                self.status_label.setText(f"Erro: {str(e)}")
        
        threading.Thread(target=run_story_conversion, daemon=True).start()
        
    def convert_to_feed(self):
        if not self.current_video:
            self.status_label.setText("Carregue um vídeo primeiro")
            return
            
        self.status_label.setText("Convertendo para formato Feed...")
        
        def run_feed_conversion():
            try:
                output_folder = Path("Visoria_Output") / "Feed_Format"
                result = self.processor.convert_to_feed(self.current_video, output_folder)
                if result:
                    self.status_label.setText(f"Conversão para Feed concluída: {result}")
                else:
                    self.status_label.setText("Erro na conversão para Feed")
            except Exception as e:
                self.status_label.setText(f"Erro: {str(e)}")
        
        threading.Thread(target=run_feed_conversion, daemon=True).start()
        
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def processing_complete(self, success, message):
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        
        if success:
            self.log_text.setText("Processamento concluído com sucesso!")
        else:
            self.log_text.setText(f"Erro no processamento: {message}")
            
    def update_highlights(self, highlights):
        # Limpar layout anterior
        for i in reversed(range(self.highlights_layout.count())):
            self.highlights_layout.itemAt(i).widget().setParent(None)
        
        if not highlights:
            placeholder = QLabel("Nenhum highlight processado")
            placeholder.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.highlights_layout.addWidget(placeholder)
        else:
            for i, highlight_path in enumerate(highlights):
                # Criar thumbnail para cada highlight
                title = f"Highlight {i+1}"
                duration = "2:30 min"  # Placeholder
                
                thumbnail = VideoThumbnail(highlight_path, title, duration)
                thumbnail.clicked.connect(self.load_highlight)
                self.highlights_layout.addWidget(thumbnail)
        
        self.highlights_layout.addStretch()
        
    def load_highlight(self, video_path):
        self.current_video = video_path
        self.player_label.setText(f"Highlight carregado: {Path(video_path).name}")
        self.status_label.setText("Highlight carregado no player principal")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Usar estilo Fusion para melhor aparência
    
    # Configurar fonte da aplicação
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = VisoriaProUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
