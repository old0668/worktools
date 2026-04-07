import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY not found in .env")
else:
    try:
        client = genai.Client(api_key=api_key)
        print("Successfully connected to Gemini API.")
        
        print("\nListing available models:")
        for model in client.models.list():
            # Print model info
            print(f"- {model}")
            
    except Exception as e:
        print(f"Error: {e}")
