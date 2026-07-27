import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta

def get_video_insights() -> str:
    """
    Fetches real YouTube Analytics data for the channel over the last 7 days 
    using the authenticated token.json.
    """
    if not os.path.exists("token.json"):
        return "No analytics available. Bot is not authenticated via OAuth yet."

    try:
        # 1. Authenticate using the generated token.json
        creds = Credentials.from_authorized_user_file("token.json")
        
        # 2. Build the Analytics API service
        youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
        
        # 3. Calculate date range (Last 7 days)
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 4. Query Channel Analytics
        response = youtube_analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration",
            dimensions="day",
            sort="-day"
        ).execute()
        
        rows = response.get("rows", [])
        if not rows:
            return "Analytics API returned no data for the last 7 days."
            
        # Get the most recent day's stats
        latest_day = rows[0]
        views = latest_day[1]
        watch_time = latest_day[2]
        avg_duration = latest_day[3]
        
        insight = f"Channel Performance (Last 24h): {views} Views, {watch_time} Mins Watched, Avg Duration: {avg_duration}s. "
        
        if avg_duration < 30:
            insight += "Audience retention is POOR. The viewers are leaving very early. CRITICAL: Start the script with massive suspense and a shocking hook immediately!"
        elif avg_duration < 60:
            insight += "Audience retention is AVERAGE. Build up the story faster in the intro."
        else:
            insight += "Audience retention is GOOD! Keep the current pacing and storytelling style."
            
        return insight
        
    except Exception as e:
        print(f"[-] Analytics Agent Error: {e}")
        return "Failed to fetch YouTube Analytics insights due to API error."

if __name__ == "__main__":
    print("[*] Testing Analytics Agent...")
    print(get_video_insights())
