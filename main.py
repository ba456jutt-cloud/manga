import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from agents.manga_scraper import search_manga, get_first_chapter_id, download_chapter_images
from agents.analytics_agent import get_video_insights
from agents.script_agent import generate_recap_script
from agents.voice_agent import generate_voiceovers
from agents.video_agent import assemble_video
from agents.thumbnail_agent import generate_manga_thumbnail
from agents.shorts_agent import generate_multiple_shorts
from agents.upload_agent import generate_seo_metadata, upload_to_youtube

def main():
    print("="*60)
    print("📖 MANGA RECAP AUTOMATION BOT V2.0")
    print("="*60)
    
    # 0. Learn from past performance
    insights = get_video_insights()
    
    # List of trending Manga to rotate through
    manga_list = [
        "Tomb Raider King", 
        "Solo Leveling", 
        "The Beginning After The End",
        "Omniscient Reader's Viewpoint",
        "Return of the Mount Hua Sect",
        "Nano Machine",
        "SSS-Class Suicide Hunter",
        "Tower of God"
    ]
    
    # State tracking file to know which manga we are on
    state_file = "manga_state.txt"
    current_idx = 0
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            current_idx = int(f.read().strip())
            
    # We need to process 1 LONG VIDEO per run (GitHub Actions will run this twice a day)
    LONG_VIDEOS_PER_DAY = 1
    
    # Global short schedule time
    # Start shorts 3 hours after the FIRST long video is uploaded
    global_schedule_time = datetime.utcnow() + timedelta(hours=3)
    
    for video_loop in range(LONG_VIDEOS_PER_DAY):
        print(f"\n============================================================")
        print(f"🎬 PROCESSING VIDEO {video_loop + 1} OF {LONG_VIDEOS_PER_DAY}")
        print(f"============================================================\n")
        
        target_manga = manga_list[current_idx % len(manga_list)]
        print(f"\n[PHASE 1] Topic Selection: {target_manga}")
        
        manga_id, synopsis = search_manga(target_manga)
        if not manga_id or not synopsis:
            print("[-] Failed to find Manga or Synopsis. Skipping...")
            current_idx += 1
            continue
            
        chapter_id = get_first_chapter_id(manga_id)
        if not chapter_id:
            print("[-] Failed to find chapter. Skipping...")
            current_idx += 1
            continue
            
        downloaded_images = download_chapter_images(chapter_id, "input")
        if not downloaded_images:
            print("[-] Failed to download images. Skipping...")
            current_idx += 1
            continue
            
        print("\n[PHASE 2] AI Story Generation (Gemini Text-Only)")
        scenes = generate_recap_script(synopsis, "input", insights)
        if not scenes:
            print("[-] Script generation failed. Skipping...")
            current_idx += 1
            continue
            
        print("\n[PHASE 3] Audio Generation (Edge-TTS)")
        scenes = generate_voiceovers(scenes, "output")
        
        print("\n[PHASE 4] Video Assembly & Rendering")
        output_file = f"output/manga_recap_{int(time.time())}.mp4"
        success = assemble_video(scenes, output_file)
        
        if success:
            print("\n[PHASE 5] SEO & Custom Thumbnail Generation")
            seo_data = generate_seo_metadata(target_manga)
            thumbnail_path = f"output/thumb_{int(time.time())}.jpg"
            thumbnail_path = generate_manga_thumbnail("input", thumbnail_path, part_num=1)
            
            print("\n[PHASE 6] Generating Multiple YouTube Shorts (9:16)")
            short_output_file = output_file.replace(".mp4", "_short.mp4")
            # Generate 4 shorts from this video
            generated_shorts = generate_multiple_shorts(scenes, num_shorts=4, base_output_path=short_output_file)
            
            print("\n[PHASE 7] YouTube Automated Upload (Long Video)")
            upload_video_id = upload_to_youtube(output_file, thumbnail_path, seo_data)
            
            if upload_video_id and generated_shorts:
                print("\n[*] Uploading and Scheduling YouTube Shorts...")
                
                # Part 1 short publishes IMMEDIATELY with the long video
                # Parts 2, 3, 4 schedule every 3 hours starting from 3 hours after upload
                short_schedule_time = datetime.utcnow() + timedelta(hours=3)
                
                for i, short_vid in enumerate(generated_shorts):
                    print(f"[*] Processing Short {i+1}/{len(generated_shorts)}")
                    
                    short_seo = seo_data.copy()
                    base_title = short_seo["title"].replace("...", "").strip()
                    short_title = f"{base_title} (Part {i+1})"
                    if len(short_title) > 85:
                        short_title = short_title[:82] + "..."
                    short_seo["title"] = short_title + " #Shorts"
                    
                    funnel_text = f"📺 Watch the FULL Video Here: https://youtu.be/{upload_video_id}\n\n"
                    short_seo["description"] = funnel_text + short_seo["description"]
                    
                    if i == 0:
                        # Part 1: Publish Public IMMEDIATELY with Long Video
                        print("    -> Part 1: Publishing Public IMMEDIATELY!")
                        upload_to_youtube(short_vid, None, short_seo, publish_at=None)
                    else:
                        # Parts 2+: Schedule every 3 hours
                        publish_at_str = short_schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                        upload_to_youtube(short_vid, None, short_seo, publish_at=publish_at_str)
                        short_schedule_time += timedelta(hours=3)
        else:
            print("[-] Video assembly failed.")
            
        current_idx += 1
        with open(state_file, "w") as f:
            f.write(str(current_idx))

    print("\n" + "="*60)
    print("✅ MANGA BOT DAILY RUN COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()
