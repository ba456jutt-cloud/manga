import os
import asyncio
import edge_tts

# Using a Hindi Male Voice suitable for storytelling/recaps
VOICE = "hi-IN-MadhurNeural"

async def _generate_audio(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="+5%")
    await communicate.save(output_path)

def generate_voiceovers(script_data: list, output_dir: str = "output") -> list:
    """Generates voiceovers for each scene in the script using Edge-TTS."""
    print("[*] Voice Agent: Generating Hindi/Urdu voiceovers...")
    os.makedirs(output_dir, exist_ok=True)
    
    updated_script = []
    
    for scene in script_data:
        scene_id = scene.get("scene_id", 1)
        text = scene.get("text", "")
        
        audio_filename = f"scene_{scene_id:03d}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        print(f"  -> Generating audio for Scene {scene_id}...")
        try:
            asyncio.run(_generate_audio(text, audio_path))
            scene["audio_path"] = audio_path
        except Exception as e:
            print(f"  [-] Failed to generate audio for scene {scene_id}: {e}")
            scene["audio_path"] = None
            
        updated_script.append(scene)
        
    print("[+] Voiceovers generated successfully.")
    return updated_script

if __name__ == "__main__":
    dummy_script = [
        {"scene_id": 1, "text": "Aaj ki kahani shuru hoti hai ek aam ladke se..."},
        {"scene_id": 2, "text": "Lekin usay nahi pata tha ke uski zindagi badalne wali hai!"}
    ]
    generate_voiceovers(dummy_script, "../output")
