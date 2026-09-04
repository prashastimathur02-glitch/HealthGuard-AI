import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")

print("Key loaded:", bool(api_key))

if not api_key:
    print("ERROR: GROQ_API_KEY was not found in .env")
    exit()

url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}"
}

r = requests.get(url, headers=headers)

print("Status code:", r.status_code)

try:
    print(r.json())
except Exception:
    print(r.text)