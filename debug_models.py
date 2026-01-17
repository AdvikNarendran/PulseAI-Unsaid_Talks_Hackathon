import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = "AIzaSyDG01gEToJPnL8x4whJ-8Ak4UREqVTzZkU"
if not api_key:
    print("Please set GEMINI_API_KEY in .env or hardcode it to test.")
else:
    genai.configure(api_key=api_key)
    try:
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
