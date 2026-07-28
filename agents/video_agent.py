import os
import subprocess
import json

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

def assemble_video(script_data: list, output_file: str = "output/manga_recap.mp4") -> bool:
    """Assembles the video using raw FFmpeg to prevent OOM errors, applying a slow pan/zoom (Ken Burns)."""
    print("[*] Video Agent: Assembling Manga Recap video...")
    image_folder = "input"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    images = sorted([f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))])
    
    if not images or not script_data:
        print("[-] Missing images or script data.")
        return False
        
    concat_file = "output/concat_list.txt"
    with open(concat_file, "w") as f:
        # Match each scene audio with an image
        # If there are more scenes than images, we loop images.
        for i, scene in enumerate(script_data):
            audio_path = scene.get("audio_path")
            if not audio_path or not os.path.exists(audio_path):
                continue
                
            duration = get_audio_duration(audio_path)
            img_file = images[i % len(images)]
            img_path = os.path.abspath(os.path.join(image_folder, img_file))
            audio_abs = os.path.abspath(audio_path)
            
            # Temporary scene video
            scene_vid = os.path.abspath(f"output/scene_vid_{i:03d}.mp4")
            
            # FFmpeg Ken Burns effect
            # zoompan: zoom in slowly from 1 to 1.1, center crop
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", img_path,
                "-i", audio_abs,
                "-vf", "scale=-2:1080,zoompan=z='min(zoom+0.0005,1.1)':d=1200",
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
    # Dummy test
    assemble_video([])
