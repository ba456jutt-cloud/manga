import os
import sqlite3
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "fugu_data.db"

def get_past_performance_feedback() -> str:
    """
    Fetches the last 3 uploaded videos from the database, retrieves their view counts
    using the public YouTube API, and returns a feedback string for Gemini.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key == "your_youtube_api_key_here":
        return "No past performance data available (API Key missing)."

    if not os.path.exists(DB_PATH):
        return "No past performance data available (Database missing)."

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if uploads table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploads'")
        if not cursor.fetchone():
            conn.close()
            return "No past videos uploaded yet."
            
        # Get last 3 uploads
        cursor.execute("SELECT upload_id, seo_title FROM uploads ORDER BY uploaded_at DESC LIMIT 3")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "No past videos uploaded yet."

        youtube = build("youtube", "v3", developerKey=api_key)
        video_ids = ",".join([row[0] for row in rows])
        
        stats_response = youtube.videos().list(
            part="statistics",
            id=video_ids
        ).execute()

        feedback_lines = []
        for row, stat in zip(rows, stats_response.get("items", [])):
            vid = row[0]
            title = row[1]
            views = int(stat["statistics"].get("viewCount", 0))
            
            if views < 100:
                performance = "POOR PERFORMANCE (Avoid similar topics)"
            elif views < 1000:
                performance = "AVERAGE PERFORMANCE (Needs better hook)"
            else:
                performance = "GOOD PERFORMANCE (Replicate this success)"
                
            feedback_lines.append(f"- Topic: '{title}' | Views: {views} | Verdict: {performance}")
            
        summary = "PAST VIDEO PERFORMANCE:\n" + "\n".join(feedback_lines)
        return summary
        
    except Exception as e:
        print(f"[-] Analytics Agent Error: {e}")
        return "Failed to fetch past performance."

if __name__ == "__main__":
    print("[*] Testing Analytics Agent...")
    print(get_past_performance_feedback())
