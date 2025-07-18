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
        
        # Build auto-editor command
        cmd = [
            "auto-editor",
            input_path,
            "--output", output_path,
            "--silence-threshold", str(silence_threshold),
            "--frame-margin", str(frame_margin),
            "--video-codec", "h264",
            "--audio-codec", "aac",
            "--temp-dir", tempfile.gettempdir()
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
            return False
            
    except Exception as e:
        logger.error(f"Error in silence removal: {str(e)}")
        return False

async def test_auto_editor():
    """Test if auto-editor is available"""
    try:
        process = await asyncio.create_subprocess_exec(
            "auto-editor", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            version = stdout.decode().strip()
            logger.info(f"Auto-editor available: {version}")
            return True
        else:
            logger.error("Auto-editor not available")
            return False
            
    except Exception as e:
        logger.error(f"Error testing auto-editor: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the module
    asyncio.run(test_auto_editor())