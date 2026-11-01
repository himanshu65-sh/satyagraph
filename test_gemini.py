
import requests
from core.config import Config

model = "gemini-3.5-flash-lite"

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{model}:generateContent"
)

headers = {
    "x-goog-api-key": Config.GEMINI_API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "contents": [{
        "parts": [{
            "text": "Reply with exactly: Gemini connection successful"
        }]
    }]
}

try:
    print("Testing model:", model)

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    print("HTTP status:", response.status_code)
    print("Response:", response.text[:1500])

except Exception as e:
    print("Error:", str(e))
