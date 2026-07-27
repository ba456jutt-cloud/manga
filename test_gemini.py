import os, json, requests, base64
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
files = [f for f in os.listdir('input') if f.endswith(('.jpg', '.png'))]
img_path = os.path.join('input', files[0])
with open(img_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")
mime_type = "image/png" if img_path.endswith(".png") else "image/jpeg"
payload = {
    "contents": [{"parts": [
        {"text": "Describe this image."},
        {"inlineData": {"mimeType": mime_type, "data": b64}}
    ]}]
}
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
print(resp.status_code)
print(resp.text)
