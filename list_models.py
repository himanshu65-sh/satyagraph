
import requests
from core.config import Config

url = "https://generativelanguage.googleapis.com/v1beta/models"

headers = {
    "x-goog-api-key": Config.GEMINI_API_KEY
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    print("\nModels supporting generateContent:\n")

    for model in data.get("models", []):
        if "generateContent" in model.get(
            "supportedGenerationMethods", []
        ):
            print(model["name"])

except Exception as e:
    print("Error:", e)
