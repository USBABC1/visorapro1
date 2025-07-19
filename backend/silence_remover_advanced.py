import os
import sys
import subprocess
import tempfile
import asyncio
from pathlib import Path
import logging
import numpy as np
import librosa
import soundfile as sf
from moviepy.editor import VideoFileClip, AudioFileClip
import json

logger = logging.getLogger(__name__)

class AdvancedSilenceRemover:
    def __init__(self):
        self.sample_rate = 22050
        self.hop_length = 512
        self.frame_length = 2048
        
    def detect_speech_patterns(self, audio_path, silence_threshold=-30):
        """Advanced speech pattern detection with restart recognition"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Calculate multiple features for better detection
            rms = librosa.feature.rms(y=y, frame_length=self.frame_length, 
                                    hop_length=self.hop_length)[0]
            
            # Spectral centroid for voice detection
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            
            # Zero crossing rate for speech detection
            zcr = librosa.feature.zero_crossing_rate(y, frame_length=self.frame_length,
                                                   hop_length=self.hop_length)[0]
            
            # Convert to dB
            rms_db = librosa.amplitude_to_db(rms, ref=np.max)
            
            # Adaptive threshold based on audio characteristics
            speech_threshold = max(silence_threshold + 5, np.percentile(rms_db, 30))
            
            # Combine features for better speech detection
            speech_frames = (rms_db > speech_threshold) & (spectral_centroids > 1000) & (zcr < 0.3)
            
            # Convert frame indices to time
            times = librosa.frames_to_time(np.arange(len(rms_db)), 
                                         sr=sr, hop_length=self.hop_length)
            
            # Find speech segments with improved logic
            speech_segments = []
            in_speech = False
            start_time = 0
            min_speech_duration = 0.3  # Minimum speech segment duration
            
            for i, is_speech in enumerate(speech_frames):
                if is_speech and not in_speech:
                    # Start of speech
                    start_time = times[i]
                    in_speech = True
                elif not is_speech and in_speech:
                    # End of speech
                    end_time = times[i]
                    duration = end_time - start_time
                    
                    # Only keep segments longer than minimum duration
                    if duration >= min_speech_duration:
                        speech_segments.append((start_time, end_time))
                    in_speech = False
            
            # Handle case where speech continues to end
            if in_speech:
                duration = times[-1] - start_time
                if duration >= min_speech_duration:
                    speech_segments.append((start_time, times[-1]))
            
            return speech_segments, rms_db, times
            
        except Exception as e:
            logger.error(f"Error in speech pattern detection: {e}")
            return [], [], []
    
    def detect_restart_patterns(self, speech_segments, rms_db, times, max_gap=4.0, min_restart_gap=0.8):
        """Detect when speaker restarts after making a mistake"""
        restart_corrections = []
        
        for i in range(len(speech_segments) - 1):
            current_start, current_end = speech_segments[i]
            next_start, next_end = speech_segments[i + 1]
            
            gap_duration = next_start - current_end
            current_duration = current_end - current_start
            next_duration = next_end - next_start
            
            # Check if this looks like a restart pattern
            if min_restart_gap <= gap_duration <= max_gap:
                # Additional checks for restart pattern
                restart_indicators = 0
                
                # 1. Next segment is significantly longer (person continues from where they left off)
                if next_duration > current_duration * 1.2:
                    restart_indicators += 1
                
                # 2. Current segment is relatively short (incomplete thought)
                if current_duration < 3.0:
                    restart_indicators += 1
                
                # 3. Gap is not too long (not a natural pause)
                if gap_duration < 2.5:
                    restart_indicators += 1
                
                # 4. Check audio energy patterns
                try:
                    current_end_idx = np.searchsorted(times, current_end)
                    next_start_idx = np.searchsorted(times, next_start)
                    
                    if current_end_idx < len(rms_db) and next_start_idx < len(rms_db):
                        # Energy should drop in the gap
                        gap_energy = np.mean(rms_db[current_end_idx:next_start_idx])
                        current_energy = np.mean(rms_db[max(0, current_end_idx-10):current_end_idx])
                        
                        if gap_energy < current_energy - 5:  # 5dB drop
                            restart_indicators += 1
                except:
                    pass
                
                # If we have enough indicators, mark as restart
                if restart_indicators >= 2:
                    restart_corrections.append({
                        'remove_start': current_start,
                        'remove_end': next_start,
                        'type': 'restart_correction',
                        'confidence': restart_indicators / 4.0,
                        'original_segments': [i, i + 1]
                    })
        
        return restart_corrections
    
    def detect_filler_words_and_hesitations(self, speech_segments, audio_path):
        """Detect and mark filler words and hesitations for removal"""
        filler_segments = []
        
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            for start, end in speech_segments:
                duration = end - start
                
                # Very short segments might be filler words
                if 0.1 <= duration <= 0.8:
                    start_sample = int(start * sr)
                    end_sample = int(end * sr)
                    segment_audio = y[start_sample:end_sample]
                    
                    # Analyze characteristics typical of filler words
                    if len(segment_audio) > 0:
                        # Low spectral complexity (filler words are usually simple sounds)
                        spectral_rolloff = librosa.feature.spectral_rolloff(y=segment_audio, sr=sr)[0]
                        avg_rolloff = np.mean(spectral_rolloff)
                        
                        # Low energy variation (filler words are usually monotone)
                        rms_var = np.var(librosa.feature.rms(y=segment_audio)[0])
                        
                        if avg_rolloff < 3000 and rms_var < 0.01:
                            filler_segments.append({
                                'start': start,
                                'end': end,
                                'type': 'filler_word',
                                'confidence': 0.7
                            })
        
        except Exception as e:
            logger.error(f"Error detecting filler words: {e}")
        
        return filler_segments
    
    def create_optimized_edit_list(self, speech_segments, restart_corrections, filler_segments, total_duration):
        """Create optimized edit list with all improvements"""
        # Start with all speech segments
        keep_segments = speech_segments.copy()
        
        # Remove segments marked for restart correction
        segments_to_remove = set()
        for restart in restart_corrections:
            if restart['confidence'] > 0.5:  # Only high-confidence corrections
                for seg_idx in restart['original_segments']:
                    if seg_idx < len(speech_segments):
                        segments_to_remove.add(seg_idx)
        
        # Remove low-confidence filler words
        for filler in filler_segments:
            if filler['confidence'] > 0.6:
                # Find and remove the corresponding segment
                for i, (start, end) in enumerate(speech_segments):
                    if abs(start - filler['start']) < 0.1 and abs(end - filler['end']) < 0.1:
                        segments_to_remove.add(i)
                        break
        
        # Filter out removed segments
        keep_segments = [seg for i, seg in enumerate(speech_segments) 
                        if i not in segments_to_remove]
        
        # Merge nearby segments with smart gap handling
        merged_segments = []
        if keep_segments:
            current_start, current_end = keep_segments[0]
            
            for start, end in keep_segments[1:]:
                gap = start - current_end
                
                # Merge if gap is very small or if it's a natural pause
                if gap < 0.3 or (gap < 1.0 and gap > 0.1):
                    current_end = end
                else:
                    merged_segments.append((current_start, current_end))
                    current_start, current_end = start, end
            
            merged_segments.append((current_start, current_end))
        
        return merged_segments

async def remove_silence_advanced(input_path: str, output_path: str, 
                                silence_threshold: int = -30, 
                                frame_margin: int = 6) -> bool:
    """Advanced silence removal with restart detection and smart editing"""
    try:
        logger.info(f"Starting advanced silence removal: {input_path}")
        
        # Initialize advanced remover
        remover = AdvancedSilenceRemover()
        
        # Extract audio for analysis
        temp_audio = tempfile.mktemp(suffix='.wav')
        video = VideoFileClip(input_path)
        
        if video.audio is None:
            logger.error("No audio track found in video")
            return False
        
        video.audio.write_audiofile(temp_audio, verbose=False, logger=None)
        
        # Detect speech patterns
        logger.info("Analyzing speech patterns with advanced detection...")
        speech_segments, rms_db, times = remover.detect_speech_patterns(temp_audio, silence_threshold)
        
        if not speech_segments:
            logger.error("No speech segments detected")
            return False
        
        logger.info(f"Detected {len(speech_segments)} speech segments")
        
        # Detect restart patterns
        logger.info("Detecting restart and error correction patterns...")
        restart_corrections = remover.detect_restart_patterns(speech_segments, rms_db, times)
        
        logger.info(f"Found {len(restart_corrections)} potential restart corrections")
        
        # Detect filler words and hesitations
        logger.info("Detecting filler words and hesitations...")
        filler_segments = remover.detect_filler_words_and_hesitations(speech_segments, temp_audio)
        
        logger.info(f"Found {len(filler_segments)} potential filler words")
        
        # Create optimized edit list
        edit_segments = remover.create_optimized_edit_list(
            speech_segments, restart_corrections, filler_segments, video.duration
        )
        
        logger.info(f"Final optimized edit list: {len(edit_segments)} segments")
        
        # Calculate time savings
        original_duration = video.duration
        edited_duration = sum(end - start for start, end in edit_segments)
        time_saved = original_duration - edited_duration
        
        logger.info(f"Time savings: {time_saved:.1f}s ({time_saved/original_duration*100:.1f}%)")
        
        # Apply edits to video
        if edit_segments:
            # Create subclips with smooth transitions
            clips = []
            for start, end in edit_segments:
                # Add frame margin
                margin_seconds = frame_margin / video.fps
                start_with_margin = max(0, start - margin_seconds)
                end_with_margin = min(video.duration, end + margin_seconds)
                
                clip = video.subclip(start_with_margin, end_with_margin)
                clips.append(clip)
            
            # Concatenate clips with crossfade for smooth transitions
            if clips:
                from moviepy.editor import concatenate_videoclips
                
                # Add small crossfades between clips for smoother transitions
                for i in range(len(clips) - 1):
                    if clips[i].duration > 0.2 and clips[i + 1].duration > 0.2:
                        clips[i] = clips[i].crossfadeout(0.05)
                        clips[i + 1] = clips[i + 1].crossfadein(0.05)
                
                final_video = concatenate_videoclips(clips, method="compose")
                
                # Write output with high quality
                final_video.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    preset="medium",
                    crf=20,  # High quality
                    verbose=False,
                    logger=None
                )
                
                # Cleanup
                final_video.close()
                for clip in clips:
                    clip.close()
        
        video.close()
        
        # Cleanup temp files
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        logger.info("Advanced silence removal completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in advanced silence removal: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test the module
    import asyncio
    
    async def test():
        success = await remove_silence_advanced("test.mp4", "output.mp4")
        print(f"Test result: {success}")
    
    asyncio.run(test())