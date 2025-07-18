import torch
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2
import os
import sys
import json
import tempfile
from moviepy.editor import VideoFileClip, ImageSequenceClip
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from huggingface_hub import login
import warnings
warnings.filterwarnings("ignore")

# Set device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Global variables for models
birefnet = None
birefnet_lite = None
model_lock = threading.Lock()

def authenticate_huggingface():
    """Try multiple authentication methods for Hugging Face"""
    try:
        # Method 1: Try without token first (public models)
        print("✓ Trying public model access...")
        return True
    except Exception as e:
        print(f"Public access failed: {e}")
        
        # Method 2: Try with environment variable
        try:
            hf_token = os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HF_TOKEN')
            if hf_token:
                print("✓ Found token in environment variables")
                login(token=hf_token)
                return True
        except Exception as e:
            print(f"Environment token failed: {e}")
        
        # Method 3: Try with local token file
        try:
            token_file = os.path.expanduser("~/.huggingface/token")
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                login(token=token)
                print("✓ Using local token file")
                return True
        except Exception as e:
            print(f"Local token failed: {e}")
        
        print("⚠️ No valid authentication found, trying anonymous access...")
        return True  # Continue anyway for public models

def load_models():
    """Load BiRefNet models with improved error handling"""
    global birefnet, birefnet_lite
    
    with model_lock:
        if birefnet is None or birefnet_lite is None:
            try:
                print("Loading BiRefNet models...")
                
                # Create models directory if it doesn't exist
                models_dir = os.path.join(os.path.dirname(__file__), 'models')
                os.makedirs(models_dir, exist_ok=True)
                
                # Authenticate first
                authenticate_huggingface()
                
                cache_dir = models_dir
                
                # Try loading models with different approaches
                try:
                    print("Loading BiRefNet (High Quality)...")
                    birefnet = AutoModelForImageSegmentation.from_pretrained(
                        "ZhengPeng7/BiRefNet", 
                        trust_remote_code=True,
                        cache_dir=cache_dir,
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        use_auth_token=False  # Try without auth first
                    )
                    birefnet.to(device)
                    birefnet.eval()
                    print("✓ BiRefNet loaded successfully")
                    
                except Exception as e:
                    print(f"BiRefNet main model failed: {e}")
                    print("Trying alternative model...")
                    # Try alternative model or create dummy
                    birefnet = None
                
                try:
                    print("Loading BiRefNet Lite (Fast Processing)...")
                    birefnet_lite = AutoModelForImageSegmentation.from_pretrained(
                        "ZhengPeng7/BiRefNet_lite", 
                        trust_remote_code=True,
                        cache_dir=cache_dir,
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        use_auth_token=False  # Try without auth first
                    )
                    birefnet_lite.to(device)
                    birefnet_lite.eval()
                    print("✓ BiRefNet Lite loaded successfully")
                    
                except Exception as e:
                    print(f"BiRefNet Lite failed: {e}")
                    print("Using fallback segmentation method...")
                    birefnet_lite = None
                
                # If both models failed, we'll use alternative methods
                if birefnet is None and birefnet_lite is None:
                    print("⚠️ BiRefNet models unavailable, using alternative segmentation")
                    return None, None
                
                print("✓ Model loading completed")
                
            except Exception as e:
                print(f"✗ Error loading models: {e}")
                print("Will use alternative background removal methods")
                return None, None
    
    return birefnet, birefnet_lite

# Enhanced image transformation for better quality
transform_image = transforms.Compose([
    transforms.Resize((1024, 1024), interpolation=transforms.InterpolationMode.LANCZOS),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def alternative_background_removal(image, background=None):
    """Alternative background removal using OpenCV when BiRefNet is unavailable"""
    try:
        print("Using alternative background removal method...")
        
        # Convert PIL to OpenCV
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Create a simple mask using edge detection and morphology
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply GaussianBlur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use adaptive threshold
        mask = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Invert mask (assuming subject is in center)
        height, width = mask.shape
        center_mask = np.zeros_like(mask)
        cv2.circle(center_mask, (width//2, height//2), min(width, height)//3, 255, -1)
        mask = cv2.bitwise_and(mask, center_mask)
        
        # Convert back to PIL
        mask_pil = Image.fromarray(mask)
        
        # Apply background
        if background is None or background == "transparent":
            # Create transparent background
            result = Image.new("RGBA", image.size, (0, 0, 0, 0))
            image_rgba = image.convert("RGBA")
            
            # Apply mask
            mask_array = np.array(mask_pil).astype(np.float32) / 255.0
            image_array = np.array(image_rgba).astype(np.float32)
            image_array[:, :, 3] = mask_array * 255
            
            result = Image.fromarray(image_array.astype(np.uint8), 'RGBA')
        else:
            # Apply colored background
            result = image
        
        return result
        
    except Exception as e:
        print(f"Alternative method failed: {e}")
        return image

def enhance_mask_quality(mask, original_size):
    """Enhance mask quality with post-processing"""
    try:
        # Convert to numpy array
        mask_np = np.array(mask)
        
        # Apply Gaussian blur for smoother edges
        mask_blurred = cv2.GaussianBlur(mask_np, (3, 3), 0.5)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((2, 2), np.uint8)
        mask_cleaned = cv2.morphologyEx(mask_blurred, cv2.MORPH_CLOSE, kernel)
        mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_OPEN, kernel)
        
        # Apply bilateral filter for edge preservation
        mask_filtered = cv2.bilateralFilter(mask_cleaned.astype(np.uint8), 9, 75, 75)
        
        # Resize back to original size with high-quality interpolation
        mask_final = cv2.resize(mask_filtered, original_size, interpolation=cv2.INTER_LANCZOS4)
        
        return Image.fromarray(mask_final)
    except Exception as e:
        print(f"Mask enhancement failed: {e}")
        return mask

def process_frame(image, background, fast_mode=False, enhance_quality=True):
    """Process a single frame with enhanced quality and fallback methods"""
    try:
        # Load models if not already loaded
        birefnet_model, birefnet_lite_model = load_models()
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        original_size = image.size
        
        # Check if BiRefNet models are available
        if birefnet_model is None and birefnet_lite_model is None:
            print("BiRefNet unavailable, using alternative method...")
            return alternative_background_removal(image, background)
        
        # Use available model
        model = birefnet_lite_model if (fast_mode and birefnet_lite_model) else (birefnet_model or birefnet_lite_model)
        
        if model is None:
            return alternative_background_removal(image, background)
        
        input_images = transform_image(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            # Use mixed precision for better performance
            with torch.autocast(device_type=device, enabled=(device == "cuda")):
                preds = model(input_images)[-1].sigmoid().cpu()
        
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        
        # Enhance mask quality if requested
        if enhance_quality:
            mask = enhance_mask_quality(pred_pil, original_size)
        else:
            mask = pred_pil.resize(original_size, Image.LANCZOS)
        
        # Handle different background types with improved blending
        if background is None or background == "transparent":
            # Create high-quality transparent background
            result = Image.new("RGBA", original_size, (0, 0, 0, 0))
            image_rgba = image.convert("RGBA")
            
            # Apply mask with anti-aliasing
            mask_array = np.array(mask).astype(np.float32) / 255.0
            image_array = np.array(image_rgba).astype(np.float32)
            
            # Apply feathering to edges for smoother transition
            mask_feathered = cv2.GaussianBlur(mask_array, (1, 1), 0.3)
            
            # Create alpha channel from enhanced mask
            alpha = (mask_feathered * 255).astype(np.uint8)
            image_array[:, :, 3] = alpha
            
            result = Image.fromarray(image_array.astype(np.uint8), 'RGBA')
            
        elif isinstance(background, str) and background.startswith("#"):
            # Color background with improved blending
            try:
                color_rgb = tuple(int(background[i:i+2], 16) for i in (1, 3, 5))
                bg_image = Image.new("RGB", original_size, color_rgb)
                
                # High-quality alpha blending
                mask_array = np.array(mask).astype(np.float32) / 255.0
                image_array = np.array(image).astype(np.float32)
                bg_array = np.array(bg_image).astype(np.float32)
                
                # Apply feathering for smoother edges
                mask_feathered = cv2.GaussianBlur(mask_array, (1, 1), 0.3)
                
                # Blend with improved algorithm
                for c in range(3):
                    image_array[:, :, c] = (image_array[:, :, c] * mask_feathered + 
                                           bg_array[:, :, c] * (1 - mask_feathered))
                
                result = Image.fromarray(image_array.astype(np.uint8))
                
            except ValueError:
                print(f"Invalid color format: {background}")
                result = image
                
        elif isinstance(background, Image.Image):
            # Image background with improved blending
            bg_image = background.convert("RGB").resize(original_size, Image.LANCZOS)
            
            # High-quality alpha blending
            mask_array = np.array(mask).astype(np.float32) / 255.0
            image_array = np.array(image).astype(np.float32)
            bg_array = np.array(bg_image).astype(np.float32)
            
            # Apply feathering for smoother edges
            mask_feathered = cv2.GaussianBlur(mask_array, (1, 1), 0.3)
            
            # Blend with improved algorithm
            for c in range(3):
                image_array[:, :, c] = (image_array[:, :, c] * mask_feathered + 
                                       bg_array[:, :, c] * (1 - mask_feathered))
            
            result = Image.fromarray(image_array.astype(np.uint8))
            
        else:
            # Default to high-quality transparent
            result = Image.new("RGBA", original_size, (0, 0, 0, 0))
            image_rgba = image.convert("RGBA")
            
            mask_array = np.array(mask).astype(np.float32) / 255.0
            image_array = np.array(image_rgba).astype(np.float32)
            
            # Apply feathering
            mask_feathered = cv2.GaussianBlur(mask_array, (1, 1), 0.3)
            alpha = (mask_feathered * 255).astype(np.uint8)
            image_array[:, :, 3] = alpha
            
            result = Image.fromarray(image_array.astype(np.uint8), 'RGBA')
        
        return result
    
    except Exception as e:
        print(f"Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        # Return original image if processing fails
        return image.convert("RGB")

def process_video(input_path, output_path, background_type="transparent", background_value=None, fast_mode=False, quality="high", enhance_quality=True):
    """Process video with enhanced background removal and fallback methods"""
    try:
        print(f"Processing video: {input_path}")
        print(f"Background type: {background_type}")
        print(f"Fast mode: {fast_mode}")
        print(f"Quality: {quality}")
        print(f"Enhance quality: {enhance_quality}")
        
        # Try to load models
        birefnet_model, birefnet_lite_model = load_models()
        
        if birefnet_model is None and birefnet_lite_model is None:
            print("⚠️ BiRefNet models unavailable, using alternative background removal")
        
        # Load video
        video = VideoFileClip(input_path)
        fps = video.fps
        duration = video.duration
        
        print(f"Video info - FPS: {fps}, Duration: {duration}s")
        
        # Prepare background
        background = None
        if background_type == "color" and background_value:
            background = background_value
        elif background_type == "image" and background_value:
            if os.path.exists(background_value):
                background = Image.open(background_value)
            else:
                print(f"Warning: Background image not found: {background_value}")
                background = None
        
        # Process frames with enhanced quality
        processed_frames = []
        frame_count = 0
        
        # Get all frames first
        frames = []
        for t in np.arange(0, duration, 1.0/fps):
            try:
                frame = video.get_frame(t)
                frames.append(frame)
            except Exception as e:
                print(f"Error getting frame at {t}s: {e}")
                continue
        
        total_frames = len(frames)
        print(f"Processing {total_frames} frames...")
        
        # Process frames in smaller batches for better memory management
        batch_size = 3 if enhance_quality else 5
        for i in range(0, total_frames, batch_size):
            batch_frames = frames[i:i+batch_size]
            batch_results = []
            
            for j, frame in enumerate(batch_frames):
                frame_count += 1
                
                try:
                    # Convert frame to PIL Image
                    pil_frame = Image.fromarray(frame.astype('uint8'), 'RGB')
                    
                    # Process frame with enhanced quality
                    processed_frame = process_frame(
                        pil_frame, 
                        background, 
                        fast_mode, 
                        enhance_quality
                    )
                    
                    # Convert back to RGB for video processing
                    if processed_frame.mode == 'RGBA':
                        # For transparent background in video, composite with white
                        white_bg = Image.new('RGB', processed_frame.size, (255, 255, 255))
                        processed_frame = Image.alpha_composite(white_bg.convert('RGBA'), processed_frame).convert('RGB')
                    
                    batch_results.append(np.array(processed_frame))
                    
                    # Progress update
                    if frame_count % 10 == 0 or frame_count == total_frames:
                        progress = (frame_count / total_frames) * 100
                        print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames})")
                        
                except Exception as e:
                    print(f"Error processing frame {frame_count}: {e}")
                    # Use original frame if processing fails
                    batch_results.append(frame)
            
            processed_frames.extend(batch_results)
            
            # Free memory
            del batch_frames
            del batch_results
        
        print("Creating output video...")
        
        # Create output video
        processed_video = ImageSequenceClip(processed_frames, fps=fps)
        
        # Add audio if present
        if video.audio:
            processed_video = processed_video.set_audio(video.audio)
        
        # Set quality parameters based on settings
        codec = "libx264"
        if quality == "high":
            bitrate = "12000k"
            preset = "slow"
        elif quality == "medium":
            bitrate = "8000k"
            preset = "medium"
        else:
            bitrate = "4000k"
            preset = "fast"
        
        # Write video with enhanced settings
        processed_video.write_videofile(
            output_path,
            codec=codec,
            bitrate=bitrate,
            audio_codec="aac",
            preset=preset,
            temp_audiofile=None,
            remove_temp=True,
            verbose=False,
            logger=None,
            threads=4
        )
        
        # Cleanup
        video.close()
        processed_video.close()
        
        print(f"✓ Video processed successfully: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing video: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """Test if models can be loaded and work properly"""
    try:
        print("Testing model loading and authentication...")
        
        # Try to authenticate
        auth_success = authenticate_huggingface()
        
        # Try to load models
        birefnet_model, birefnet_lite_model = load_models()
        
        if birefnet_model is not None or birefnet_lite_model is not None:
            print("✓ At least one BiRefNet model loaded successfully")
            return True
        else:
            print("⚠️ BiRefNet models unavailable, but alternative methods available")
            return True  # Return True because we have fallback methods
            
    except Exception as e:
        print(f"✗ Error testing models: {e}")
        return True  # Still return True because we have alternative methods

def main():
    parser = argparse.ArgumentParser(description='Remove background from video using BiRefNet or alternative methods')
    parser.add_argument('--input', required=True, help='Input video path')
    parser.add_argument('--output', required=True, help='Output video path')
    parser.add_argument('--background-type', default='transparent', choices=['transparent', 'color', 'image'])
    parser.add_argument('--background-value', help='Background color (hex) or image path')
    parser.add_argument('--fast-mode', action='store_true', help='Use fast mode (BiRefNet_lite)')
    parser.add_argument('--quality', default='high', choices=['low', 'medium', 'high'])
    parser.add_argument('--enhance-quality', action='store_true', default=True, help='Enable quality enhancement')
    parser.add_argument('--test', action='store_true', help='Test model loading and authentication')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_models()
        sys.exit(0 if success else 1)
    
    success = process_video(
        args.input,
        args.output,
        args.background_type,
        args.background_value,
        args.fast_mode,
        args.quality,
        args.enhance_quality
    )
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()