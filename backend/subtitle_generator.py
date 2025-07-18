import os
import sys
import asyncio
import tempfile
from pathlib import Path
import logging
import whisper
import torch

logger = logging.getLogger(__name__)

# Global model cache
whisper_model = None
model_lock = asyncio.Lock()

async def load_whisper_model(model_size: str = "base"):
    """Load Whisper model with caching"""
    global whisper_model
    
    async with model_lock:
        if whisper_model is None:
            try:
                logger.info(f"Loading Whisper model: {model_size}")
                
                # Check if CUDA is available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Using device: {device}")
                
                # Load model
                whisper_model = whisper.load_model(model_size, device=device)
                logger.info("Whisper model loaded successfully")
                
            except Exception as e:
                logger.error(f"Error loading Whisper model: {str(e)}")
                raise
    
    return whisper_model

def format_timestamp(seconds: float) -> str:
    """Format timestamp for SRT format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def create_srt_content(segments) -> str:
    """Create SRT subtitle content from Whisper segments"""
    srt_content = []
    
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()
        
        srt_content.append(f"{i}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(text)
        srt_content.append("")  # Empty line between subtitles
    
    return "\n".join(srt_content)

async def generate_subtitles(input_path: str, output_path: str, language: str = "pt") -> bool:
    """
    Generate subtitles from video using Whisper
    
    Args:
        input_path: Path to input video
        output_path: Path to output SRT file
        language: Language code (pt, en, es, etc.)
    
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Starting subtitle generation: {input_path}")
        
        # Load Whisper model
        model = await load_whisper_model("base")
        
        # Transcribe audio
        logger.info("Transcribing audio...")
        result = model.transcribe(
            input_path,
            language=language,
            word_timestamps=True,
            verbose=False
        )
        
        # Create SRT content
        srt_content = create_srt_content(result['segments'])
        
        # Write SRT file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logger.info(f"Subtitles generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating subtitles: {str(e)}")
        return False

async def test_whisper():
    """Test if Whisper is available"""
    try:
        model = await load_whisper_model("tiny")  # Use tiny model for testing
        logger.info("Whisper is available and working")
        return True
    except Exception as e:
        logger.error(f"Whisper test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the module
    asyncio.run(test_whisper())