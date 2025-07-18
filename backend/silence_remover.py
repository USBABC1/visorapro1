import os
import sys
import subprocess
import tempfile
import asyncio
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

async def remove_silence(input_path: str, output_path: str, silence_threshold: int = -30, frame_margin: int = 6) -> bool:
    """
    Remove silence from video using auto-editor
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        silence_threshold: Silence detection threshold in dB
        frame_margin: Frames to keep before/after cuts
    
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Starting silence removal: {input_path}")
        
        # Build auto-editor command with correct parameters
        cmd = [
            "auto-editor",
            input_path,
            "--output_file", output_path,
            "--silent_threshold", str(abs(silence_threshold) / 100.0),  # Convert dB to 0-1 range
            "--frame_margin", str(frame_margin),
            "--video_codec", "h264",
            "--audio_codec", "aac",
            "--temp_dir", tempfile.gettempdir(),
            "--no_open"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run auto-editor
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info("Silence removal completed successfully")
            return True
        else:
            logger.error(f"Auto-editor failed: {stderr.decode()}")
            
            # Try alternative command format
            logger.info("Trying alternative auto-editor command format...")
            alt_cmd = [
                "auto-editor",
                input_path,
                "--output_file", output_path,
                "--silent_speed", "99999",  # Effectively removes silent parts
                "--frame_margin", str(frame_margin),
                "--no_open"
            ]
            
            alt_process = await asyncio.create_subprocess_exec(
                *alt_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            alt_stdout, alt_stderr = await alt_process.communicate()
            
            if alt_process.returncode == 0:
                logger.info("Alternative auto-editor command succeeded")
                return True
            else:
                logger.error(f"Alternative auto-editor also failed: {alt_stderr.decode()}")
                return False
            return False
            
    except Exception as e:
        logger.error(f"Error in silence removal: {str(e)}")
        return False

async def ffmpeg_silence_removal(input_path: str, output_path: str, silence_threshold: int = -30, frame_margin: int = 6) -> bool:
    """
    Fallback silence removal using FFmpeg silencedetect and silenceremove filters
    """
    try:
        logger.info(f"Using FFmpeg fallback for silence removal: {input_path}")
        
        # Convert dB to linear scale for FFmpeg
        silence_level = 10 ** (silence_threshold / 20)
        
        # Build FFmpeg command for silence removal
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-af", f"silenceremove=start_periods=1:start_duration=0:start_threshold={silence_level}:detection=peak,aformat=dblp,areverse,silenceremove=start_periods=1:start_duration=0:start_threshold={silence_level}:detection=peak,aformat=dblp,areverse",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-y",  # Overwrite output file
            output_path
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info("FFmpeg silence removal completed successfully")
            return True
        else:
            logger.error(f"FFmpeg silence removal failed: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Error in FFmpeg silence removal: {str(e)}")
        return False

async def test_auto_editor():
    """Test if auto-editor is available"""
    try:
        # First try to get help to see available options
        process = await asyncio.create_subprocess_exec(
            "auto-editor", "--help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            help_text = stdout.decode().strip()
            logger.info("Auto-editor is available")
            # Log some of the help text to understand available options
            logger.info(f"Auto-editor help (first 500 chars): {help_text[:500]}")
            return True
        else:
            logger.error(f"Auto-editor help failed: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing auto-editor: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the module
    asyncio.run(test_auto_editor())