import os
import json
import requests
from dotenv import load_dotenv
import math

load_dotenv()

def generate_recap_script(synopsis: str, input_dir: str = "input", insights: str = "") -> list:
    """Uses Gemini to generate a Hindi/Urdu recap script from TEXT, completely avoiding image uploads."""
    print("[*] Script Agent: Generating script from text synopsis...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[-] Fatal Error: GEMINI_API_KEY not found.")
        return []
    api_key = api_key.strip()
        
    image_files = sorted([f for f in os.listdir(input_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    if not image_files:
        print("[-] No images found in input directory. Cannot generate script.")
        return []
        
    print(f"[*] Found {len(image_files)} pages in input. Sending ONLY text summary to Gemini...")
    
    parts = []
    
    learning_prompt = ""
    if insights:
        print("[*] Applying learning insights to prompt...")
        learning_prompt = f"\nCRITICAL INSTRUCTION based on past video performance:\n{insights}\nEnsure the new script addresses this feedback.\n"

    prompt_text = f"""
    You are an expert Manga/Manhwa YouTube Recap scriptwriter.
    I want you to write a suspenseful, engaging, and dramatic script for a YouTube video in Roman Urdu/Hindi.
    {learning_prompt}
    Here is the story summary:
    "{synopsis}"
    
    Break this story down into EXACTLY {min(len(image_files), 15)} scenes (or segments).
    Each scene should have a few sentences of narration.
    
    OUTPUT FORMAT (STRICT JSON ONLY, NO MARKDOWN):
    [
      {{
        "scene_id": 1,
        "text": "The Hindi/Urdu narration text for this scene...",
        "emotion": "dramatic"
      }}
    ]
    """
    parts.append({"text": prompt_text})
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        
        result_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        script_data = json.loads(result_text)
        
        print("[+] Script generated successfully from TEXT!")
        
        # Now map the generated scenes to the downloaded images
        # so the video agent can stitch them together.
        for i, scene in enumerate(script_data):
            img_idx = int(i * (len(image_files) / len(script_data)))
            img_idx = min(img_idx, len(image_files) - 1)
            scene["image_path"] = os.path.join(input_dir, image_files[img_idx])
            
        return script_data
        
    except Exception as e:
        print(f"[-] Script Generation failed: {e}")
        return []

if __name__ == "__main__":
    test_synopsis = "A boy wakes up in a dungeon with the ability to level up. He fights monsters and becomes the strongest hunter."
    script = generate_recap_script(test_synopsis, "../input")
    print(json.dumps(script, indent=2, ensure_ascii=False))
