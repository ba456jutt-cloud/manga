import os
from agents.video_agent import assemble_video, get_audio_duration

def generate_multiple_shorts(scenes: list, num_shorts: int = 4, base_output_path: str = "output/short_video.mp4") -> list:
    print(f"[*] Shorts Agent: Preparing up to {num_shorts} YouTube Shorts...")
    
    generated_shorts = []
    
    # Try to extract sequential blocks of scenes, each under 60 seconds
    scene_idx = 0
    short_idx = 1
    
    while scene_idx < len(scenes) and short_idx <= num_shorts:
        total_dur = 0
        current_chunk = []
        
        while scene_idx < len(scenes):
            s = scenes[scene_idx]
            audio_path = s.get("audio_path")
            if not audio_path or not os.path.exists(audio_path):
                scene_idx += 1
                continue
                
            dur = get_audio_duration(audio_path) + 0.1
            
            # If adding this scene exceeds 59 seconds, stop the chunk here
            if total_dur + dur > 59.0:
                # Unless the chunk is empty, in which case this single scene is >59s
                if not current_chunk:
                    print(f"[-] Warning: Scene {s.get('id')} is longer than 59s alone. Skipping for short.")
                    scene_idx += 1
                    continue
                break
                
            current_chunk.append(s)
            total_dur += dur
            scene_idx += 1
            
        if not current_chunk:
            break
            
        print(f"[*] Compiling Short #{short_idx} ({len(current_chunk)} scenes, {total_dur:.2f}s)...")
        
        # Generate filename like short_video_1.mp4, short_video_2.mp4
        name, ext = os.path.splitext(base_output_path)
        chunk_path = f"{name}_{short_idx}{ext}"
        
        success = assemble_video(current_chunk, chunk_path, is_short=True)
        if success and os.path.exists(chunk_path):
            generated_shorts.append(chunk_path)
            
        short_idx += 1
        
    print(f"[+] Successfully generated {len(generated_shorts)} shorts.")
    return generated_shorts
