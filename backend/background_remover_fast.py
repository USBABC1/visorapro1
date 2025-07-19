import cv2
import numpy as np
import os
import sys
import tempfile
from moviepy.editor import VideoFileClip, ImageSequenceClip
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path
import time

# Fast background removal using OpenCV and optimized algorithms
class FastBackgroundRemover:
    def __init__(self):
        # Use MOG2 background subtractor for speed
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=25, detectShadows=False
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.frame_buffer = []
        self.buffer_size = 10
        
    def process_frame_fast(self, frame, background_type="transparent", background_value=None):
        """Process single frame with maximum speed optimization"""
        try:
            # Resize for processing speed (CapCut-style optimization)
            height, width = frame.shape[:2]
            process_scale = 0.5 if min(height, width) > 720 else 0.75
            process_height = int(height * process_scale)
            process_width = int(width * process_scale)
            
            # Resize for processing
            small_frame = cv2.resize(frame, (process_width, process_height), 
                                   interpolation=cv2.INTER_LINEAR)
            
            # Apply background subtraction
            fg_mask = self.background_subtractor.apply(small_frame, learningRate=0.01)
            
            # Fast morphological operations
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel, iterations=1)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel, iterations=1)
            
            # Fast edge refinement
            fg_mask = cv2.medianBlur(fg_mask, 3)
            
            # Resize mask back to original size
            fg_mask = cv2.resize(fg_mask, (width, height), interpolation=cv2.INTER_LINEAR)
            
            # Apply mask with optimized blending
            if background_type == "transparent":
                # Create RGBA image
                result = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                result[:, :, 3] = fg_mask
            elif background_type == "color" and background_value:
                # Apply color background with fast blending
                try:
                    color_rgb = tuple(int(background_value[i:i+2], 16) for i in (1, 3, 5))
                    background = np.full_like(frame, color_rgb[::-1])  # BGR format
                    
                    # Fast normalized blending
                    mask_norm = fg_mask.astype(np.float32) / 255.0
                    mask_inv = 1.0 - mask_norm
                    
                    # Vectorized blending
                    result = (frame.astype(np.float32) * mask_norm[:, :, np.newaxis] + 
                             background.astype(np.float32) * mask_inv[:, :, np.newaxis]).astype(np.uint8)
                except:
                    result = frame
            else:
                result = frame
                
            return result
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return frame

def process_video_fast(input_path, output_path, background_type="transparent", background_value=None):
    """Ultra-fast video processing optimized like CapCut"""
    try:
        print(f"Starting ultra-fast background removal: {input_path}")
        
        # Load video with optimizations
        video = VideoFileClip(input_path)
        fps = video.fps
        duration = video.duration
        
        print(f"Video info - FPS: {fps}, Duration: {duration}s")
        
        # Initialize background remover
        bg_remover = FastBackgroundRemover()
        
        # Process frames with maximum speed
        processed_frames = []
        frame_count = 0
        total_frames = int(fps * duration)
        
        print(f"Processing {total_frames} frames with ultra-fast algorithm...")
        
        # Use larger steps for preview frames to build background model quickly
        preview_step = max(1, total_frames // 50)
        for i in range(0, min(50, total_frames), preview_step):
            t = i / fps
            if t < duration:
                frame = video.get_frame(t)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                bg_remover.background_subtractor.apply(frame_bgr, learningRate=0.1)
        
        # Process all frames
        for t in np.arange(0, duration, 1.0/fps):
            try:
                frame = video.get_frame(t)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Process frame
                processed_frame = bg_remover.process_frame_fast(
                    frame_bgr, background_type, background_value
                )
                
                # Convert back to RGB
                if background_type == "transparent":
                    processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGRA2RGBA)
                    # For video, composite with white background
                    white_bg = np.ones_like(processed_frame_rgb[:,:,:3]) * 255
                    alpha = processed_frame_rgb[:,:,3:4] / 255.0
                    processed_frame_rgb = (processed_frame_rgb[:,:,:3] * alpha + 
                                         white_bg * (1 - alpha)).astype(np.uint8)
                else:
                    processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                processed_frames.append(processed_frame_rgb)
                
                frame_count += 1
                if frame_count % 15 == 0:  # Update more frequently
                    progress = (frame_count / total_frames) * 100
                    print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames})")
                    
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
                processed_frames.append(frame)
        
        print("Creating output video with ultra-fast encoding...")
        
        # Create output video with maximum speed settings
        processed_video = ImageSequenceClip(processed_frames, fps=fps)
        
        # Add audio if present
        if video.audio:
            processed_video = processed_video.set_audio(video.audio)
        
        # Write with ultra-fast settings (CapCut-style)
        processed_video.write_videofile(
            output_path,
            codec="libx264",
            preset="ultrafast",  # Maximum speed
            bitrate="6000k",     # Balanced quality/speed
            audio_codec="aac",
            temp_audiofile=None,
            remove_temp=True,
            verbose=False,
            logger=None,
            threads=8
        )
        
        # Cleanup
        video.close()
        processed_video.close()
        
        print(f"✓ Ultra-fast background removal completed: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error in ultra-fast background removal: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Ultra-fast background removal')
    parser.add_argument('--input', required=True, help='Input video path')
    parser.add_argument('--output', required=True, help='Output video path')
    parser.add_argument('--background-type', default='transparent', choices=['transparent', 'color'])
    parser.add_argument('--background-value', help='Background color (hex)')
    
    args = parser.parse_args()
    
    start_time = time.time()
    success = process_video_fast(
        args.input,
        args.output,
        args.background_type,
        args.background_value
    )
    end_time = time.time()
    
    print(f"Processing time: {end_time - start_time:.2f} seconds")
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()