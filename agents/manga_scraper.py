import os
import requests
import time

def search_manga(title: str) -> tuple:
    print(f"[*] Searching MangaDex for '{title}'...")
    url = f"https://api.mangadex.org/manga?title={title}&limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            manga = data["data"][0]
            manga_id = manga["id"]
            manga_title = manga["attributes"]["title"].get("en", title)
            # Try to get English description
            desc = manga["attributes"]["description"].get("en", "")
            if not desc:
                # Fallback to any available description
                desc = next(iter(manga["attributes"]["description"].values()), "A mysterious manga full of action and suspense.")
                
            print(f"[+] Found Manga: {manga_title} (ID: {manga_id})")
            return manga_id, desc
    print("[-] Manga not found.")
    return None, None

def get_first_chapter_id(manga_id: str) -> str:
    url = f"https://api.mangadex.org/manga/{manga_id}/feed?translatedLanguage[]=en&order[chapter]=asc&limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["data"]:
            chapter_id = data["data"][0]["id"]
            chapter_num = data["data"][0]["attributes"]["chapter"]
            print(f"[+] Found First Chapter: {chapter_num} (ID: {chapter_id})")
            return chapter_id
    print("[-] No English chapters found.")
    return None

def download_chapter_images(chapter_id: str, output_dir: str = "input") -> list:
    print(f"[*] Fetching pages for Chapter ID: {chapter_id}...")
    url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("[-] Failed to get chapter pages.")
        return []
        
    data = response.json()
    base_url = data["baseUrl"]
    hash_id = data["chapter"]["hash"]
    pages = data["chapter"]["data"]
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear old images in input dir
    for f in os.listdir(output_dir):
        if f.endswith(".jpg") or f.endswith(".png"):
            os.remove(os.path.join(output_dir, f))
            
    downloaded_files = []
    print(f"[*] Downloading {len(pages)} pages...")
    for i, page in enumerate(pages):
        img_url = f"{base_url}/data/{hash_id}/{page}"
        img_path = os.path.join(output_dir, f"page_{i+1:03d}.jpg")
        
        # MangaDex requests 100ms delay between image downloads
        time.sleep(0.2)
        
        try:
            r = requests.get(img_url)
            if r.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(r.content)
                downloaded_files.append(img_path)
                print(f"  -> Saved {img_path}")
            else:
                print(f"  [-] Failed to download page {i+1}")
        except Exception as e:
            print(f"  [-] Error downloading page {i+1}: {e}")
            
    print(f"[+] Successfully downloaded {len(downloaded_files)} pages.")
    return downloaded_files

if __name__ == "__main__":
    # Test script: Downloads the first chapter
    manga_id, synopsis = search_manga("Tomb Raider King")
    if manga_id:
        print(f"Synopsis: {synopsis[:100]}...")
        chapter_id = get_first_chapter_id(manga_id)
        if chapter_id:
            download_chapter_images(chapter_id, "../input")
