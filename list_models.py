import google.generativeai as genai
from app.core.config import get_settings

def list_models():
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")

if __name__ == "__main__":
    list_models()
