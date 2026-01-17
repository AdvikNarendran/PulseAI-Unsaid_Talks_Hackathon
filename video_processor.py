import os
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip

# Fix for some environments where mp.solutions is not loaded automatically
try:
    from mediapipe.python import solutions as mp_solutions
except ImportError:
    mp_solutions = mp.solutions if hasattr(mp, "solutions") else None

def detect_face_center(frame, face_detection):
    """Detects the center x-coordinate of the largest face in the frame."""
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)
        
        if results.detections:
            # Find the largest detection
            largest_detection = max(results.detections, key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
            bbox = largest_detection.location_data.relative_bounding_box
            center_x = bbox.xmin + (bbox.width / 2)
            return center_x
    except Exception as e:
        pass
    return 0.5 # Default to center

import textwrap

def burn_subtitles(clip, subtitles):
    """
    Burns subtitles into the video clip using PIL for better text rendering.
    subtitles: list of dicts {'start': float, 'end': float, 'text': str}
    """
    def make_text_frame(get_frame, t):
        frame = get_frame(t) # numpy array [h, w, 3]
        
        # Find active subtitle
        current_text = None
        for sub in subtitles:
            if sub['start'] <= t <= sub['end']:
                current_text = sub['text']
                break
        
        if not current_text:
            return frame
            
        # Convert to PIL
        pil_img = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_img)
        
        w, h = pil_img.size
        
        # Dynamic Font Size (e.g., 4% of height) creates readable text for vertical video
        fontsize = int(h * 0.04)
        try:
            # Try load a standard font
            font = ImageFont.truetype("arial.ttf", fontsize)
        except:
            font = ImageFont.load_default()
            
        # Wrap text to ensure it fits frame (approx 25 chars for vertical video is safe)
        lines = textwrap.wrap(current_text, width=25)
        
        # Calculate sizing for all lines
        line_metrics = [] # (width, height, text)
        total_block_h = 0
        
        for line in lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                lw = bbox[2] - bbox[0]
                lh = bbox[3] - bbox[1]
            except:
                # Fallback for older PIL
                lw, lh = draw.textsize(line, font=font)
            
            line_metrics.append((lw, lh, line))
            total_block_h += lh + 10 # 10px spacing
            
        total_block_h -= 10 # Remove last spacing
        
        # Top-left of the text block (Centered Horizontally, Bottom 20% Vertically)
        start_y = h - (h * 0.20) - (total_block_h / 2)
        
        current_y = start_y
        for lw, lh, line in line_metrics:
            x = (w - lw) / 2
            
            # Draw with thick outline (Stroke)
            stroke_width = max(2, int(fontsize * 0.1))
            draw.text((x, current_y), line, font=font, fill='white', stroke_width=stroke_width, stroke_fill='black')
            
            current_y += lh + 10
        
        return np.array(pil_img)

    return clip.fl(lambda gf, t: make_text_frame(gf, t))


def resize_to_letterbox_vertical(clip, target_w=1080, target_h=1920):
    """
    Resizes the clip to fit inside the target 9:16 box while maintaining aspect ratio (Letterbox).
    Adds black bars.
    """
    # 1. Resize to fit width
    clip_resized = clip.resize(width=target_w)
    
    # If height > target_h (unlikely for landscape, but possible), fit by height
    if clip_resized.h > target_h:
        clip_resized = clip.resize(height=target_h)
        
    # 2. Center on black background
    # Since we avoid full CompositeVideoClip if possible for speed, but here we need it for bars.
    # Note: MoviePy TextClip and CompositeVideoClip can be heavy.
    
    # Calculate position to center
    x_pos = (target_w - clip_resized.w) // 2
    y_pos = (target_h - clip_resized.h) // 2
    
    # Create composite
    # Ideally we'd use a ColorClip as background, but for simplicity/speed let's just make the clip larger?
    # No, Composition is best.
    
    # Workaround if ColorClip is missing imports or robust check: 
    # Just return the resized clip if we don't strictly need the black bars file-size overhead?
    # User said "put the whole frame in the aspect ratio".
    # Vertical platforms handles 9:16.
    
    # Let's try to just use `margin` fx if available, or just Composite.
    final = CompositeVideoClip([clip_resized.set_position("center")], size=(target_w, target_h))
    return final

def crop_to_vertical_with_face_tracking(clip):
    """
    Crops a clip to 9:16 vertical ratio, tracking the face.
    """
    if mp_solutions is None:
        print("MediaPipe solutions not found, defaulting to center crop.")
        w, h = clip.size
        # Fallback calc
        target_w = h * (9/16)
        x1 = (w / 2) - (target_w / 2)
        x2 = (w / 2) + (target_w / 2)
        return clip.crop(x1=x1, y1=0, x2=x2, y2=h)
        
    mp_face_detection = mp_solutions.face_detection
    
    # Use "short range" (0) or "full range" (1). 1 is better for standard videos.
    # We wrap in Try/Except to ensure we ALWAYS return a clip
    try:
        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
            w, h = clip.size
            target_ratio = 9/16
            target_w = h * target_ratio
            
            # Sample face positions
            centers = []
            timestamps = [0, clip.duration/2, max(0, clip.duration - 0.1)]
            
            for t in timestamps:
                try:
                    frame = clip.get_frame(t)
                    c = detect_face_center(frame, face_detection)
                    centers.append(c)
                except:
                    centers.append(0.5)
            
            # Average center
            avg_center = sum(centers) / len(centers) if centers else 0.5
            
            # Calculate Crop
            center_pix = avg_center * w
            x1 = center_pix - (target_w / 2)
            x2 = center_pix + (target_w / 2)
            
            # Clamp
            if x1 < 0:
                x1 = 0
                x2 = target_w
            if x2 > w:
                x2 = w
                x1 = w - target_w
                
            return clip.crop(x1=x1, y1=0, x2=x2, y2=h)
            
    except Exception as e:
        print(f"Face tracking crashed: {e}. Fallback to center.")
        w, h = clip.size
        target_w = h * (9/16)
        x1 = (w / 2) - (target_w / 2)
        x2 = (w / 2) + (target_w / 2)
        return clip.crop(x1=x1, y1=0, x2=x2, y2=h)

def process_video(video_path, clips_metadata, transcript_segments=None, output_dir="generated_clips", use_subs=True, max_clip_duration=60, crop_mode="Letterbox"):
    """
    Cuts, Formats (Letterbox/Crop), Enforces Duration, and Adds Subtitles.
    crop_mode: "Letterbox" (All visible) or "Face Tracking" (Zoomed)
    transcript_segments: list of dicts from Whisper {'start': float, 'end': float, 'text': str}
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generated_files = []
    
    try:
        original_clip = VideoFileClip(video_path)
        
        for i, meta in enumerate(clips_metadata):
            start = meta.get('start_time')
            end = meta.get('end_time')
            
            if start is None or end is None:
                continue
            
            # --- Enforce Duration Constraint (Dynamic) ---
            duration = end - start
            if duration > max_clip_duration:
                end = start + max_clip_duration
            
            # 1. Cut
            clip = original_clip.subclip(start, end)
            
            # 2. Aspect Ratio Formatting
            if crop_mode == "Face Tracking" and clip.w > clip.h:
                # Zoom/Crop
                clip = crop_to_vertical_with_face_tracking(clip)
            else:
                # Default: Fit to Screen / Letterbox (User Preference)
                clip = resize_to_letterbox_vertical(clip)
            
            # 3. Burn Subtitles (Real Speech Sync)
            if use_subs:
                clip_subs = []
                if transcript_segments:
                    # Filter segments that are inside this clip's time range
                    # We add a small buffer (0.5s) to catch words just on the edge
                    for seg in transcript_segments:
                        seg_start = seg['start']
                        seg_end = seg['end']
                        
                        # Check intersection
                        # If segment overlaps with [start, end]
                        if (seg_start < end) and (seg_end > start):
                            # Adjust relative to clip start
                            rel_start = max(0, seg_start - start)
                            rel_end = min(clip.duration, seg_end - start)
                            
                            clip_subs.append({
                                'start': rel_start,
                                'end': rel_end,
                                'text': seg['text'].strip()
                            })
                
                # Fallback if no transcript provided or no speech found in segment
                if not clip_subs:
                     text_content = meta.get('quote') or meta.get('summary') or ""
                     if text_content:
                        clip_subs = [{'start': 0, 'end': clip.duration, 'text': text_content}]
                
                if clip_subs:
                    clip = burn_subtitles(clip, clip_subs)

            output_filename = os.path.join(output_dir, f"clip_{i+1}_{int(start)}.mp4")
            clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")
            generated_files.append(output_filename)
            
        original_clip.close()
        return generated_files

    except Exception as e:
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()
        return []
