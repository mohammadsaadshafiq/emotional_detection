import os
import sys
import requests
import json
from dotenv import load_dotenv
from tqdm import tqdm
from github import Github

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
    print("Error: GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO must be set in .env file.")
    sys.exit(1)

# Initialize GitHub client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")

def load_metadata(file_path):
    """Load GIF metadata from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)

def download_gif(gif_id):
    url = f"https://media.giphy.com/media/{gif_id}/giphy.gif"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Error downloading {gif_id}: {response.status_code}")
        return None

def upload_to_github(gif_id, gif_content):
    path = f"{gif_id}.gif"
    try:
        # Check if the file already exists (avoids duplicates)
        contents = repo.get_contents(path)
        print(f"Skipping {gif_id}: File already exists at {path}")
        return contents.download_url
    except Exception:
        # Upload if it doesn't exist
        repo.create_file(
            path=path,
            message=f"Add {gif_id}.gif",
            content=gif_content,
            branch="main"
        )
        return f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/{path}"

def main():
    # Load your existing JSON metadata
    metadata_path = "gif_metadata.json"
    json_data = load_metadata(metadata_path)
    
    # Track uploaded URLs
    new_json_data = {emotion: [] for emotion in json_data.keys()}

    for emotion, gif_ids in json_data.items():
        for gif_id in tqdm(gif_ids, desc=f"Processing {emotion}"):
            # Download
            gif_content = download_gif(gif_id)
            if not gif_content:
                continue

            # Upload
            imgur_url = upload_to_github(gif_id, gif_content)
            if imgur_url:
                new_json_data[emotion].append(imgur_url)
            else:
                print(f"Failed to upload {gif_id}")

    # Save the updated JSON with GitHub URLs
    with open("new_gif_urls.json", "w") as f:
        json.dump(new_json_data, f, indent=2)
    print("Done! New JSON saved to 'new_gif_urls.json'")

if __name__ == "__main__":
    main()