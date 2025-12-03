import asyncio
import sys
from pathlib import Path
import uuid

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from apps.api.services import service
from apps.api.database import db

async def main():
    audio_path = Path(r"C:\Users\User\Desktop\audio2txt\dataset_samples\1015小組顧問.m4a")
    if not audio_path.exists():
        print(f"File not found: {audio_path}")
        return

    print(f"Testing v4.0 pipeline with: {audio_path.name}")
    
    # 1. Create a task ID
    task_id = str(uuid.uuid4())
    print(f"Created Task ID: {task_id}")
    
    # 2. Initialize task in DB (simulating the API endpoint)
    db.create_task(task_id, str(audio_path), "universal_summary")
    
    # 3. Run processing
    print("Starting processing (this calls AssemblyAI cloud)...")
    try:
        await service.process_audio(task_id, str(audio_path), "universal_summary")
        print("Processing function returned.")
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Check result
    task = db.get_task(task_id)
    if task:
        print(f"\nStatus: {task['status']}")
        print(f"Progress: {task['progress']}%")
        
        if task['status'] == 'completed':
            result = task['result']
            print("\n--- Result Summary ---")
            print(f"Duration: {result.get('duration')} seconds")
            print(f"Speakers: {result.get('speakers')}")
            print(f"Summary Preview: {result.get('summary')[:100]}...")
            print(f"Report Path: {result.get('report_path')}")
            print(f"Transcript Path: {result.get('transcript_path')}")
            
            # Read the report content to show it worked
            report_path = Path(result.get('report_path'))
            if report_path.exists():
                print("\n--- Report Content (First 500 chars) ---")
                print(report_path.read_text(encoding='utf-8')[:500])
        else:
            print(f"Error Message: {task.get('error_message')}")

if __name__ == "__main__":
    asyncio.run(main())
