import os
import subprocess
import json
from PIL import Image, ImageFilter

def get_audio_duration(audio_path: str) -> float:
    """Uses ffprobe to get the duration of an audio file in seconds."""
    if not os.path.exists(audio_path):
        return 5.0 # Fallback 5 seconds
        
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"[-] FFprobe error for {audio_path}: {e}")
        return 5.0

def preprocess_manga_frame(img_path: str, target_w: int, target_h: int) -> str:
    """
    Intelligently processes tall webtoon/manga pages:
    1. Creates a beautiful blurred background filling target_w x target_h.
    2. Crops/scales the panel to fit gracefully in the center.
    Saves to a processed temp image file and returns its path.
    """
    processed_dir = os.path.abspath("output/processed_frames")
    os.makedirs(processed_dir, exist_ok=True)
    filename = os.path.basename(img_path)
    out_path = os.path.join(processed_dir, f"{target_w}x{target_h}_{filename}")
    
    if os.path.exists(out_path):
        return out_path
        
    try:
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        
        # 1. Create Blurred Background (Fills 100% of target_w x target_h)
        ratio_bg = max(target_w / w, target_h / h)
        bg_w, bg_h = int(w * ratio_bg), int(h * ratio_bg)
        bg = img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
        
        left_bg = (bg_w - target_w) // 2
        top_bg = (bg_h - target_h) // 2
        bg = bg.crop((left_bg, top_bg, left_bg + target_w, top_bg + target_h))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        
        # 2. Prepare Foreground Panel
        # Webtoon images are often super tall strips (h > w * 1.5)
        if h > w * 1.5:
            # Crop upper portion (1.3 aspect ratio) where main characters & speech bubbles are
            crop_h = int(w * 1.3)
            fg_crop = img.crop((0, 0, w, min(h, crop_h)))
        else:
            fg_crop = img
            
        fg_w, fg_h = fg_crop.size
        
        # Scale foreground to fit target_h (with margin)
        max_fg_h = int(target_h * 0.96)
        ratio_fg = max_fg_h / fg_h
        new_fg_w = int(fg_w * ratio_fg)
        new_fg_h = max_fg_h
        
        if new_fg_w > target_w:
            ratio_fg = target_w / fg_w
            new_fg_w = target_w
            new_fg_h = int(fg_h * ratio_fg)
            
        fg_resized = fg_crop.resize((new_fg_w, new_fg_h), Image.Resampling.LANCZOS)
        
        # Paste centered on blurred background
        paste_x = (target_w - new_fg_w) // 2
        paste_y = (target_h - new_fg_h) // 2
        bg.paste(fg_resized, (paste_x, paste_y))
        
        bg.save(out_path, quality=95)
        return out_path
    except Exception as e:
        print(f"[-] Image preprocessing error for {img_path}: {e}")
        return img_path

def assemble_video(script_data: list, output_file: str = "output/manga_recap.mp4", is_short: bool = False) -> bool:
    """Assembles the video using raw FFmpeg with preprocessed blurred backdrop frames."""
    print("[*] Video Agent: Assembling Manga Recap video...")
    image_folder = "input"
    
    target_w, target_h = (1080, 1920) if is_short else (1920, 1080)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    images = sorted([f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))])
    
    if not images or not script_data:
        print("[-] Missing images or script data.")
        return False
        
    concat_file = "output/concat_list.txt"
    with open(concat_file, "w") as f:
        for i, scene in enumerate(script_data):
            audio_path = scene.get("audio_path")
            if not audio_path or not os.path.exists(audio_path):
                continue
                
            duration = get_audio_duration(audio_path)
            img_file = images[i % len(images)]
            raw_img_path = os.path.abspath(os.path.join(image_folder, img_file))
            audio_abs = os.path.abspath(audio_path)
            
            # Preprocess frame with PIL (Blurred Backdrop + Smart Panel Crop)
            processed_img_path = preprocess_manga_frame(raw_img_path, target_w, target_h)
            
            # Temporary scene video
            scene_vid = os.path.abspath(f"output/scene_vid_{i:03d}.mp4")
            
            # FFmpeg smooth zoompan filter on pre-framed canvas
            vf_filter = f"zoompan=z='min(zoom+0.001,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1200:s={target_w}x{target_h},fps=30"
                
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", processed_img_path,
                "-i", audio_abs,
                "-vf", vf_filter,
                "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
                "-b:a", "192k", "-pix_fmt", "yuv420p",
                "-shortest", "-t", str(duration + 0.2),
                scene_vid
            ]
            print(f"  -> Rendering Scene {i+1} ({duration:.1f}s)...")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(scene_vid):
                f.write(f"file '{scene_vid}'\n")
                
    print("[*] Concatenating scenes into final video...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_file
    ]
    
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(output_file):
        print(f"[+] Manga Recap Video successfully saved to: {output_file}")
        return True
    else:
        print("[-] Video assembly failed.")
        return False

if __name__ == "__main__":
    assemble_video([])
