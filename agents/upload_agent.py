import os
import json
import requests
from dotenv import load_dotenv
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

# OAuth scopes required for uploading videos and setting thumbnails
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secrets.json"

def get_authenticated_service():
    """Authenticates the user and returns the YouTube API service object."""
    credentials = None
    
    # Check if we already have a saved token
    if os.path.exists("token.json"):
        with open("token.json", "r") as f:
            credentials = Credentials.from_authorized_user_info(json.load(f), SCOPES)
            
    # If no valid credentials available, ask user to log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"[-] Fatal Error: '{CLIENT_SECRETS_FILE}' not found. Cannot authenticate.")
                return None
            print("\n[*] Upload Agent: Initiating Google OAuth Login Flow...")
            print("[!] PLEASE CHECK YOUR BROWSER AND LOG IN TO YOUTUBE.")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            # Port 0 means it will randomly select an open port for the local server
            credentials = flow.run_local_server(port=0)
            
        # Save the credentials for future automated runs
        with open("token.json", "w") as f:
            f.write(credentials.to_json())
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

def generate_seo_metadata(topic: str) -> dict:
    """Uses Gemini to generate SEO title, description, and tags."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return _fallback_seo(topic)

    print(f"[*] Upload Agent: Generating SEO metadata for '{topic}'...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are an expert YouTube SEO manager. We just created a viral Hindi Manga Recap video about: "{topic}".
    Generate the metadata for this video in JSON format.
    
    Requirements:
    1. "title": A hyper-viral, dramatic, and extremely clickbaity YouTube title (under 95 characters). Use extreme curiosity gaps. Example: "He Was Betrayed But Returned As A GOD!" DO NOT use generic or academic titles.
    2. "description": A captivating, highly detailed, and LONG description (at least 300 words). Write it in Roman Urdu/Hindi. Explain the topic like you are telling a fascinating story to a friend. CRITICAL: You MUST include a minimum of 20 hashtags at the bottom. These hashtags MUST include #manga, #manhwa, #recap alongside highly searched anime/manga hashtags.
    3. "tags": A list of exactly 20 highly searched YouTube tags/keywords related to Manga Recaps (e.g. manga recap hindi, manhwa explanation).
    
    OUTPUT FORMAT (Strict JSON only, no markdown blocks):
    {{
      "title": "...",
      "description": "...",
      "tags": ["...", "..."]
    }}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}
    
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
            response.raise_for_status()
            result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # Clean markdown codeblocks if Gemini added them
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            metadata = json.loads(result_text)
            
            # CRITICAL: YouTube limits titles to 100 characters. Force limit to 95.
            if len(metadata.get("title", "")) > 95:
                metadata["title"] = metadata["title"][:92] + "..."
                
            # SEO HACK: Inject Watch Next links to revive old videos
            from agents.db_agent import get_recent_uploads
            recent_vids = get_recent_uploads(3)
            if recent_vids:
                watch_next_text = "\\n\\n📺 WATCH NEXT:\\n"
                for vid in recent_vids:
                    watch_next_text += f"🔗 {vid['title']} - https://youtu.be/{vid['id']}\\n"
                
                # Prepend the links so they are visible above the fold
                metadata["description"] = watch_next_text + "\\n" + metadata.get("description", "")
                
            print("[+] SEO Metadata generated successfully.")
            return metadata
        except Exception as e:
            print(f"  [-] SEO Generation attempt {attempt+1} failed: {e}. Retrying...")
            import time
            time.sleep(5)
            
    print("[-] SEO Generation completely failed. Using fallback.")
    return _fallback_seo(topic)

def _fallback_seo(topic: str):
    return {
        "title": f"The Ultimate Review of {topic}",
        "description": f"Explore the amazing story of {topic} in this epic recap. Join us on a mind-bending journey!\n\n#Manga #Manhwa #Recap #Anime #Explanation #Hindi #Urdu",
        "tags": ["manga", "manhwa", "recap", "anime", "explanation", "hindi", "urdu", "story", "summary"]
    }

def upload_to_youtube(video_path: str, thumbnail_path: str, seo_data: dict, publish_at: str = None) -> str:
    """Authenticates, uploads video, sets thumbnail, and returns the YouTube Video ID."""
    if not os.path.exists(video_path):
        print(f"[-] Upload Agent Error: Video file '{video_path}' not found.")
        return None

    youtube = get_authenticated_service()
    if not youtube:
        return None
        
    print(f"\n[*] Upload Agent: Starting Upload to YouTube...")
    print(f"    Title: {seo_data['title']}")
    if publish_at:
        print(f"    Scheduled for: {publish_at}")
    
    # 1. Upload Video
    status_obj = {
        "privacyStatus": "private" if publish_at else "public",
        "selfDeclaredMadeForKids": False
    }
    if publish_at:
        status_obj["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": seo_data["title"],
            "description": seo_data["description"],
            "tags": seo_data["tags"],
            "categoryId": "24"  # 24 is Entertainment
        },
        "status": status_obj
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    
    response = None
    try:
        print("[*] Uploading video... (This might take a few minutes)")
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  ... Uploaded {int(status.progress() * 100)}%")
                
        video_id = response.get("id")
        print(f"[+] Video Uploaded successfully! Video ID: {video_id}")
        print(f"[+] YouTube Link: https://youtu.be/{video_id}")
        
    except googleapiclient.errors.HttpError as e:
        print(f"[-] An HTTP error {e.resp.status} occurred:\n{e.content}")
        return None
        
    # 2. Upload Thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        print("[*] Upload Agent: Setting custom thumbnail...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("[+] Custom thumbnail set successfully.")
        except Exception as e:
            print(f"[-] Failed to set thumbnail: {e}")
            
    return video_id

if __name__ == "__main__":
    # Test Upload
    print("Test run disabled directly. Call from main.py")
