import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from apps.api.engines.openai_engine import OpenAISummaryEngine

# Load env vars
load_dotenv()

async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        return

    print(f"Testing OpenAI Engine with key: {api_key[:10]}...")
    
    engine = OpenAISummaryEngine(api_key)
    
    # Read existing transcript
    transcript_path = Path(r"C:\Users\User\Desktop\audio2txt\output\api_results\fdee15a8-184d-4c36-a1cf-4297ded8554b\transcript.txt")
    if not transcript_path.exists():
        print("Transcript not found")
        return
        
    transcript_text = transcript_path.read_text(encoding='utf-8')
    print(f"Read transcript: {len(transcript_text)} chars")
    
    print("Generating summary...")
    try:
        summary = await engine.generate_summary(transcript_text)
        print("\n--- Summary Generated Successfully ---")
        print(summary[:500])
        print("...")
    except Exception as e:
        print(f"\nError generating summary: {e}")

if __name__ == "__main__":
    asyncio.run(main())
