import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The scopes required for YouTube Upload and YouTube Analytics
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

def main():
    print("="*50)
    print("Manga Bot YouTube Authentication")
    print("="*50)
    
    if not os.path.exists("client_secrets.json"):
        print("[-] Error: 'client_secrets.json' not found in current directory.")
        print("Please download it from Google Cloud Console and place it here.")
        return
        
    print("[*] Opening browser for Google Login...")
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    # This will open the user's browser, wait for login, and save the credentials.
    credentials = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open("token.json", "w") as token_file:
        token_file.write(credentials.to_json())
        
    print("[+] Authentication Successful! 'token.json' has been created.")
    print("You can now safely run main.py")

if __name__ == "__main__":
    main()
