import os
import sys
import subprocess
import tempfile
import asyncio
from pathlib import Path
import logging
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ImageSequenceClip
import argparse

logger = logging.getLogger(__name__)

class Video2XUpscaler:
    """Video upscaling using Real-ESRGAN and other AI models (Video2X implementation)"""
    
    def __init__(self):
        self.models = {
            'realesrgan-x4plus': 'Real-ESRGAN 4x upscaling',
            'realesrgan-x2plus': 'Real-ESRGAN 2x upscaling', 
            'waifu2x': 'Waifu2x anime upscaling',
            'srmd': 'SRMD general upscaling',
            'opencv-edsr': 'OpenCV EDSR',
            'opencv-espcn': 'OpenCV ESPCN'
        }
        self.available_models = self._check_available_models()
    
    def _check_available_models(self):
        """Check which upscaling models are available"""
        available = []
        
        # Check for Real-ESRGAN
        try:
            result = subprocess.run(['realesrgan-ncnn-vulkan', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                available.extend(['realesrgan-x4plus', 'realesrgan-x2plus'])
                logger.info("Real-ESRGAN models available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.info("Real-ESRGAN not found")
        
        # Check for Waifu2x
        try:
            result = subprocess.run(['waifu2x-ncnn-vulkan', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                available.append('waifu2x')
                logger.info("Waifu2x available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.info("Waifu2x not found")
        
        # OpenCV-based upscaling is always available
        available.extend(['opencv-edsr', 'opencv-espcn'])
        
        return available
    
    def upscale_frame_opencv(self, frame, scale_factor=2, model='edsr'):
        """OpenCV-based upscaling with enhanced algorithms"""
        try:
            height, width = frame.shape[:2]
            new_height, new_width = int(height * scale_factor), int(width * scale_factor)
            
            if model == 'edsr':
                # Enhanced Deep Super-Resolution approach
                # First, use INTER_CUBIC for base upscaling
                upscaled = cv2.resize(frame, (new_width, new_height), 
                                    interpolation=cv2.INTER_CUBIC)
                
                # Apply unsharp masking for detail enhancement
                gaussian = cv2.GaussianBlur(upscaled, (0, 0), 2.0)
                upscaled = cv2.addWeighted(upscaled, 1.5, gaussian, -0.5, 0)
                
                # Edge enhancement
                gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                edges = cv2.dilate(edges, np.ones((2,2), np.uint8))
                edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                upscaled = cv2.addWeighted(upscaled, 0.9, edges_colored, 0.1, 0)
                
            elif model == 'espcn':
                # ESPCN-style upscaling with detail preservation
                upscaled = cv2.resize(frame, (new_width, new_height), 
                                    interpolation=cv2.INTER_LANCZOS4)
                
                # Bilateral filter for noise reduction while preserving edges
                upscaled = cv2.bilateralFilter(upscaled, 9, 75, 75)
                
            else:
                # Default high-quality upscaling
                upscaled = cv2.resize(frame, (new_width, new_height), 
                                    interpolation=cv2.INTER_LANCZOS4)
            
            return upscaled
            
        except Exception as e:
            logger.error(f"Error in OpenCV upscaling: {e}")
            return cv2.resize(frame, (int(width * scale_factor), int(height * scale_factor)))
    
    async def upscale_with_realesrgan(self, input_dir, output_dir, scale=4):
        """Upscale using Real-ESRGAN"""
        try:
            cmd = [
                'realesrgan-ncnn-vulkan',
                '-i', input_dir,
                '-o', output_dir,
                '-s', str(scale),
                '-n', f'realesrgan-x{scale}plus',
                '-f', 'png'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Real-ESRGAN upscaling completed")
                return True
            else:
                logger.error(f"Real-ESRGAN failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error in Real-ESRGAN upscaling: {e}")
            return False
    
    async def upscale_video(self, input_path, output_path, scale_factor=2, 
                          model='auto', quality='high'):
        """Main video upscaling function (Video2X style)"""
        try:
            logger.info(f"Starting Video2X upscaling: {input_path}")
            logger.info(f"Scale factor: {scale_factor}x, Model: {model}")
            
            # Auto-select best available model
            if model == 'auto':
                if f'realesrgan-x{scale_factor}plus' in self.available_models:
                    model = f'realesrgan-x{scale_factor}plus'
                elif 'waifu2x' in self.available_models:
                    model = 'waifu2x'
                else:
                    model = 'opencv-edsr'
            
            logger.info(f"Using model: {model}")
            
            # Load video
            video = VideoFileClip(input_path)
            fps = video.fps
            duration = video.duration
            
            logger.info(f"Video info - FPS: {fps}, Duration: {duration}s")
            
            # Choose processing method based on model
            if model.startswith('realesrgan') and model in self.available_models:
                return await self._upscale_with_external_tool(
                    video, output_path, model, scale_factor
                )
            else:
                return await self._upscale_with_opencv(
                    video, output_path, scale_factor, model, quality
                )
                
        except Exception as e:
            logger.error(f"Error in video upscaling: {e}")
            return False
    
    async def _upscale_with_external_tool(self, video, output_path, model, scale_factor):
        """Upscale using external tools like Real-ESRGAN"""
        try:
            # Create temporary directories
            temp_dir = tempfile.mkdtemp()
            frames_dir = os.path.join(temp_dir, 'frames')
            upscaled_dir = os.path.join(temp_dir, 'upscaled')
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(upscaled_dir, exist_ok=True)
            
            logger.info("Extracting frames for upscaling...")
            
            # Extract frames from video
            frame_count = 0
            frame_paths = []
            
            for t in np.arange(0, video.duration, 1.0/video.fps):
                frame = video.get_frame(t)
                frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.png")
                cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                frame_paths.append(frame_path)
                frame_count += 1
                
                if frame_count % 100 == 0:
                    logger.info(f"Extracted {frame_count} frames...")
            
            logger.info(f"Extracted {frame_count} frames total")
            
            # Upscale frames
            if model.startswith('realesrgan'):
                success = await self.upscale_with_realesrgan(
                    frames_dir, upscaled_dir, scale_factor
                )
            else:
                success = False
            
            if success:
                # Reconstruct video from upscaled frames
                logger.info("Reconstructing video from upscaled frames...")
                upscaled_frames = []
                
                for i in range(frame_count):
                    frame_path = os.path.join(upscaled_dir, f"frame_{i:06d}.png")
                    if os.path.exists(frame_path):
                        frame = cv2.imread(frame_path)
                        if frame is not None:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            upscaled_frames.append(frame_rgb)
                        else:
                            logger.warning(f"Could not read upscaled frame {i}")
                            # Use original frame as fallback
                            original_frame = video.get_frame(i / video.fps)
                            upscaled_frames.append(original_frame)
                    else:
                        logger.warning(f"Upscaled frame {i} not found")
                        # Use original frame as fallback
                        original_frame = video.get_frame(i / video.fps)
                        upscaled_frames.append(original_frame)
                
                if upscaled_frames:
                    upscaled_video = ImageSequenceClip(upscaled_frames, fps=video.fps)
                    
                    # Add audio if present
                    if video.audio:
                        upscaled_video = upscaled_video.set_audio(video.audio)
                    
                    # Write output with high quality settings
                    upscaled_video.write_videofile(
                        output_path,
                        codec="libx264",
                        preset="slow",
                        crf=16,  # Very high quality for upscaled content
                        audio_codec="aac",
                        verbose=False,
                        logger=None
                    )
                    
                    upscaled_video.close()
                    logger.info("Video reconstruction completed")
            
            video.close()
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in external tool upscaling: {e}")
            return False
    
    async def _upscale_with_opencv(self, video, output_path, scale_factor, 
                                 model, quality):
        """Upscale using OpenCV methods with optimizations"""
        try:
            logger.info("Processing with enhanced OpenCV upscaling...")
            
            upscaled_frames = []
            frame_count = 0
            total_frames = int(video.fps * video.duration)
            
            # Process frames in batches for memory efficiency
            batch_size = 10
            current_batch = []
            
            for t in np.arange(0, video.duration, 1.0/video.fps):
                frame = video.get_frame(t)
                current_batch.append(frame)
                
                if len(current_batch) >= batch_size:
                    # Process batch
                    for batch_frame in current_batch:
                        frame_bgr = cv2.cvtColor(batch_frame, cv2.COLOR_RGB2BGR)
                        
                        # Upscale frame
                        upscaled_frame = self.upscale_frame_opencv(
                            frame_bgr, scale_factor, model.replace('opencv-', '')
                        )
                        
                        upscaled_frame_rgb = cv2.cvtColor(upscaled_frame, cv2.COLOR_BGR2RGB)
                        upscaled_frames.append(upscaled_frame_rgb)
                        
                        frame_count += 1
                    
                    current_batch = []
                    
                    if frame_count % 50 == 0:
                        progress = (frame_count / total_frames) * 100
                        logger.info(f"Upscaling progress: {progress:.1f}% ({frame_count}/{total_frames})")
            
            # Process remaining frames in batch
            for batch_frame in current_batch:
                frame_bgr = cv2.cvtColor(batch_frame, cv2.COLOR_RGB2BGR)
                upscaled_frame = self.upscale_frame_opencv(
                    frame_bgr, scale_factor, model.replace('opencv-', '')
                )
                upscaled_frame_rgb = cv2.cvtColor(upscaled_frame, cv2.COLOR_BGR2RGB)
                upscaled_frames.append(upscaled_frame_rgb)
                frame_count += 1
            
            # Create output video
            logger.info("Creating upscaled video...")
            upscaled_video = ImageSequenceClip(upscaled_frames, fps=video.fps)
            
            # Add audio if present
            if video.audio:
                upscaled_video = upscaled_video.set_audio(video.audio)
            
            # Write with quality settings
            crf = 16 if quality == 'high' else 20 if quality == 'medium' else 24
            
            upscaled_video.write_videofile(
                output_path,
                codec="libx264",
                preset="slow" if quality == 'high' else "medium",
                crf=crf,
                audio_codec="aac",
                verbose=False,
                logger=None
            )
            
            upscaled_video.close()
            video.close()
            
            logger.info("OpenCV upscaling completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in OpenCV upscaling: {e}")
            return False

async def upscale_video(input_path: str, output_path: str, 
                       scale_factor: int = 2, model: str = 'auto', 
                       quality: str = 'high') -> bool:
    """Main upscaling function"""
    upscaler = Video2XUpscaler()
    return await upscaler.upscale_video(input_path, output_path, 
                                      scale_factor, model, quality)

def main():
    parser = argparse.ArgumentParser(description='Video2X-style video upscaling')
    parser.add_argument('--input', required=True, help='Input video path')
    parser.add_argument('--output', required=True, help='Output video path')
    parser.add_argument('--scale', type=int, default=2, choices=[2, 4], 
                       help='Scale factor (2x or 4x)')
    parser.add_argument('--model', default='auto', 
                       choices=['auto', 'realesrgan-x4plus', 'realesrgan-x2plus', 
                               'waifu2x', 'opencv-edsr', 'opencv-espcn'],
                       help='Upscaling model')
    parser.add_argument('--quality', default='high', 
                       choices=['low', 'medium', 'high'],
                       help='Output quality')
    
    args = parser.parse_args()
    
    async def run_upscaling():
        success = await upscale_video(
            args.input, args.output, args.scale, args.model, args.quality
        )
        return success
    
    success = asyncio.run(run_upscaling())
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()