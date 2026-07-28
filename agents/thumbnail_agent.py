import os
import random
from PIL import Image, ImageDraw, ImageFont
import requests

def get_bold_font(size=100):
    os.makedirs("assets", exist_ok=True)
    font_path = "assets/Anton-Regular.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
        try:
            r = requests.get(url)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except:
            return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def generate_manga_thumbnail(input_dir="input", output_path="output/thumbnail.jpg", part_num=1):
    """
    Creates a thumbnail by stitching 2 manga images side by side,
    similar to popular Manga Recap channels.
    """
    print("[*] Thumbnail Agent: Generating high-CTR Manga thumbnail...")
    
    # Get all images
    images = sorted([f for f in os.listdir(input_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    if not images:
        print("[-] No images found in input/ for thumbnail.")
        return None
        
    # Use the first image (usually the chapter cover, which is highest quality)
    cover_path = os.path.join(input_dir, images[0])
    
    try:
        img = Image.open(cover_path).convert("RGBA")
    except Exception as e:
        print(f"[-] Failed to open image: {e}")
        return None

    # Target thumbnail size
    canvas_w, canvas_h = 1280, 720
    
    # Resize and crop to fill the thumbnail canvas
    img_w, img_h = img.size
    ratio = max(canvas_w / img_w, canvas_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Crop to center top (since manga covers usually have the character face near the top)
    left = (new_w - canvas_w) / 2
    right = (new_w + canvas_w) / 2
    top = 0  # Crop from top
    bottom = canvas_h
    
    canvas = img.crop((left, top, right, bottom))
    
    # Add Dark Gradient (Vignette) at the bottom for text readability
    gradient = Image.new('RGBA', (canvas_w, canvas_h), color=0)
    draw = ImageDraw.Draw(gradient)
    for y in range(int(canvas_h * 0.5), canvas_h):
        alpha = int(255 * ((y - canvas_h * 0.5) / (canvas_h * 0.5)))
        draw.line([(0, y), (canvas_w, y)], fill=(0, 0, 0, alpha))
    
    canvas = Image.alpha_composite(canvas, gradient)
    
    # Add Massive Clickable Text
    draw = ImageDraw.Draw(canvas)
    font_large = get_bold_font(180)
    font_small = get_bold_font(90)
    
    # Helper to draw text with thick black outline
    def draw_text_with_outline(d, x, y, text, font, fill_color, stroke=10):
        for dx in range(-stroke, stroke+1):
            for dy in range(-stroke, stroke+1):
                d.text((x+dx, y+dy), text, font=font, fill="black")
        d.text((x, y), text, font=font, fill=fill_color)
        
    # "EPISODE X" or "PART X"
    top_text = f"EPISODE {part_num}"
    draw_text_with_outline(draw, 50, canvas_h - 320, top_text, font_small, "white", stroke=6)
    
    # Highly clickable buzzword
    buzzwords = ["OVERPOWERED!", "REBORN!", "UNSTOPPABLE!", "AWAKENED!", "REVENGE!"]
    main_text = random.choice(buzzwords)
    draw_text_with_outline(draw, 50, canvas_h - 220, main_text, font_large, "#FFD700", stroke=12) # Gold/Yellow
    
    # Save
    canvas = canvas.convert("RGB")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, quality=95)
    
    print(f"[+] Thumbnail saved successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_manga_thumbnail("../input", "../output/thumbnail_test.jpg")
