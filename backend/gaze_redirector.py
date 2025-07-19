import os
import sys
import cv2
import numpy as np
import tempfile
from moviepy.editor import VideoFileClip, ImageSequenceClip
import argparse
import logging
import asyncio

logger = logging.getLogger(__name__)

class GazeRedirector:
    """Gaze redirection for video using facial landmarks and eye tracking"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Try to load more advanced face detection if available
        try:
            import dlib
            self.use_dlib = True
            self.face_detector = dlib.get_frontal_face_detector()
            
            # Try to load facial landmark predictor
            predictor_path = "shape_predictor_68_face_landmarks.dat"
            if os.path.exists(predictor_path):
                self.landmark_predictor = dlib.shape_predictor(predictor_path)
                self.has_landmarks = True
            else:
                self.has_landmarks = False
                logger.info("Facial landmark predictor not found, using basic detection")
                
        except ImportError:
            self.use_dlib = False
            self.has_landmarks = False
            logger.info("dlib not available, using OpenCV cascade classifiers")
    
    def detect_faces_and_eyes(self, frame):
        """Detect faces and eyes in frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        if self.use_dlib:
            # Use dlib for better face detection
            faces = self.face_detector(gray)
            face_rects = [(face.left(), face.top(), face.width(), face.height()) for face in faces]
        else:
            # Use OpenCV cascade
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            face_rects = faces
        
        face_data = []
        
        for (x, y, w, h) in face_rects:
            face_roi_gray = gray[y:y+h, x:x+w]
            face_roi_color = frame[y:y+h, x:x+w]
            
            # Detect eyes within face region
            eyes = self.eye_cascade.detectMultiScale(face_roi_gray, 1.1, 5)
            
            if len(eyes) >= 2:
                # Sort eyes by x-coordinate (left to right)
                eyes = sorted(eyes, key=lambda eye: eye[0])
                
                face_data.append({
                    'face_rect': (x, y, w, h),
                    'eyes': eyes,
                    'face_roi': face_roi_color
                })
        
        return face_data
    
    def estimate_gaze_direction(self, eye_region):
        """Estimate gaze direction from eye region"""
        try:
            gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_RGB2GRAY)
            
            # Apply threshold to find pupil (darkest region)
            _, thresh = cv2.threshold(gray_eye, 50, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find largest contour (likely the pupil)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get centroid of pupil
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    pupil_x = int(M["m10"] / M["m00"])
                    pupil_y = int(M["m01"] / M["m00"])
                    
                    # Calculate relative position within eye
                    eye_center_x = gray_eye.shape[1] // 2
                    eye_center_y = gray_eye.shape[0] // 2
                    
                    # Normalize gaze direction (-1 to 1)
                    gaze_x = (pupil_x - eye_center_x) / (gray_eye.shape[1] / 2)
                    gaze_y = (pupil_y - eye_center_y) / (gray_eye.shape[0] / 2)
                    
                    return gaze_x, gaze_y
            
            return 0.0, 0.0
            
        except Exception as e:
            logger.error(f"Error estimating gaze: {e}")
            return 0.0, 0.0
    
    def redirect_gaze(self, frame, face_data, target_direction=0.0):
        """Redirect gaze to target direction"""
        try:
            result_frame = frame.copy()
            
            for face_info in face_data:
                face_x, face_y, face_w, face_h = face_info['face_rect']
                eyes = face_info['eyes']
                
                for (ex, ey, ew, eh) in eyes:
                    # Convert eye coordinates to global frame coordinates
                    global_ex = face_x + ex
                    global_ey = face_y + ey
                    
                    # Extract eye region
                    eye_region = frame[global_ey:global_ey+eh, global_ex:global_ex+ew]
                    
                    if eye_region.size > 0:
                        # Estimate current gaze
                        current_gaze_x, current_gaze_y = self.estimate_gaze_direction(eye_region)
                        
                        # Calculate adjustment needed
                        adjustment_x = target_direction - current_gaze_x
                        
                        # Apply gaze redirection if adjustment is significant
                        if abs(adjustment_x) > 0.1:
                            redirected_eye = self.apply_gaze_shift(eye_region, adjustment_x, 0)
                            result_frame[global_ey:global_ey+eh, global_ex:global_ex+ew] = redirected_eye
            
            return result_frame
            
        except Exception as e:
            logger.error(f"Error redirecting gaze: {e}")
            return frame
    
    def apply_gaze_shift(self, eye_region, shift_x, shift_y):
        """Apply gaze shift to eye region"""
        try:
            h, w = eye_region.shape[:2]
            
            # Calculate pixel shift
            pixel_shift_x = int(shift_x * w * 0.2)  # 20% of eye width max
            pixel_shift_y = int(shift_y * h * 0.2)  # 20% of eye height max
            
            # Create transformation matrix
            M = np.float32([[1, 0, pixel_shift_x], [0, 1, pixel_shift_y]])
            
            # Apply transformation to eye region
            shifted_eye = cv2.warpAffine(eye_region, M, (w, h), borderMode=cv2.BORDER_REFLECT)
            
            # Blend with original for more natural look
            alpha = 0.7  # Blend factor
            result = cv2.addWeighted(shifted_eye, alpha, eye_region, 1 - alpha, 0)
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying gaze shift: {e}")
            return eye_region
    
    def process_frame(self, frame, target_gaze_direction=0.0):
        """Process single frame for gaze redirection"""
        try:
            # Detect faces and eyes
            face_data = self.detect_faces_and_eyes(frame)
            
            if not face_data:
                return frame
            
            # Redirect gaze for all detected faces
            result = self.redirect_gaze(frame, face_data, target_gaze_direction)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame

async def redirect_gaze_video(input_path: str, output_path: str, 
                            target_direction: float = 0.0) -> bool:
    """Main gaze redirection function"""
    try:
        logger.info(f"Starting gaze redirection: {input_path}")
        logger.info(f"Target direction: {target_direction}")
        
        # Initialize gaze redirector
        redirector = GazeRedirector()
        
        # Load video
        video = VideoFileClip(input_path)
        fps = video.fps
        duration = video.duration
        
        logger.info(f"Video info - FPS: {fps}, Duration: {duration}s")
        
        # Process frames
        processed_frames = []
        frame_count = 0
        total_frames = int(fps * duration)
        
        logger.info(f"Processing {total_frames} frames for gaze redirection...")
        
        for t in np.arange(0, duration, 1.0/fps):
            try:
                frame = video.get_frame(t)
                
                # Process frame for gaze redirection
                processed_frame = redirector.process_frame(frame, target_direction)
                processed_frames.append(processed_frame)
                
                frame_count += 1
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"Progress: {progress:.1f}% ({frame_count}/{total_frames})")
                    
            except Exception as e:
                logger.error(f"Error processing frame {frame_count}: {e}")
                # Use original frame if processing fails
                processed_frames.append(frame)
        
        logger.info("Creating output video...")
        
        # Create output video
        processed_video = ImageSequenceClip(processed_frames, fps=fps)
        
        # Add audio if present
        if video.audio:
            processed_video = processed_video.set_audio(video.audio)
        
        # Write output
        processed_video.write_videofile(
            output_path,
            codec="libx264",
            preset="medium",
            crf=20,
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        
        # Cleanup
        video.close()
        processed_video.close()
        
        logger.info(f"✓ Gaze redirection completed: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error in gaze redirection: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Gaze redirection for video')
    parser.add_argument('--input', required=True, help='Input video path')
    parser.add_argument('--output', required=True, help='Output video path')
    parser.add_argument('--target-direction', type=float, default=0.0, 
                       help='Target gaze direction (-1.0 to 1.0)')
    
    args = parser.parse_args()
    
    async def run_redirection():
        success = await redirect_gaze_video(
            args.input, args.output, args.target_direction
        )
        return success
    
    success = asyncio.run(run_redirection())
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()