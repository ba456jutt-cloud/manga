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
    print("[*] Thumbnail Agent: Generating side-by-side Manga thumbnail...")
    
    # Get all images
    images = [f for f in os.listdir(input_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    if len(images) < 2:
        print("[-] Not enough images in input/ to stitch a thumbnail.")
        return None
        
    # Pick 2 random images
    selected = random.sample(images, 2)
    img1_path = os.path.join(input_dir, selected[0])
    img2_path = os.path.join(input_dir, selected[1])
    
    # Open images
    try:
        img1 = Image.open(img1_path).convert("RGBA")
        img2 = Image.open(img2_path).convert("RGBA")
    except Exception as e:
        print(f"[-] Failed to open images: {e}")
        return None

    # Target thumbnail size
    canvas_w, canvas_h = 1280, 720
    canvas = Image.new("RGBA", (canvas_w, canvas_h), "black")
    
    # Resize both images to fill half the canvas
    # Half width = 640
    def resize_and_crop(img, target_w, target_h):
        img_w, img_h = img.size
        # Calculate aspect ratio
        ratio = max(target_w / img_w, target_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Crop to center
        left = (new_w - target_w) / 2
        top = (new_h - target_h) / 2
        right = (new_w + target_w) / 2
        bottom = (new_h + target_h) / 2
        return img.crop((left, top, right, bottom))
        
    left_img = resize_and_crop(img1, 640, 720)
    right_img = resize_and_crop(img2, 640, 720)
    
    # Paste on canvas
    canvas.paste(left_img, (0, 0))
    canvas.paste(right_img, (640, 0))
    
    # Draw a white separator line in the middle
    draw = ImageDraw.Draw(canvas)
    draw.line([(640, 0), (640, 720)], fill="white", width=15)
    
    # Add Text (English is best for CTR)
    font = get_bold_font(100) # Slightly smaller text as requested
    
    # Helper to draw text with thick black outline
    def draw_text_with_outline(d, x, y, text, font, fill_color):
        stroke = 8
        for dx in range(-stroke, stroke+1):
            for dy in range(-stroke, stroke+1):
                d.text((x+dx, y+dy), text, font=font, fill="black")
        d.text((x, y), text, font=font, fill=fill_color)
        
    # Left Side Text: e.g. "DAY-1" or "PART 1"
    left_text = f"DAY-{part_num}"
    draw_text_with_outline(draw, 100, 50, left_text, font, "#FFFF00") # Yellow
    
    # Right Side Text: e.g. "HINDI"
    right_text = "HINDI"
    draw_text_with_outline(draw, 740, 50, right_text, font, "#FFFF00") # Yellow
    
    # Add a small part number tag at bottom left
    font_small = get_bold_font(70)
    draw_text_with_outline(draw, 50, 600, f"#{part_num}", font_small, "white")
    
    # Save
    canvas = canvas.convert("RGB")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, quality=95)
    
    print(f"[+] Thumbnail saved successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_manga_thumbnail("../input", "../output/thumbnail_test.jpg")
