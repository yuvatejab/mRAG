"""Quick WebSocket Progress Test"""
import asyncio
import json
import requests
import websockets
from pathlib import Path
import uuid

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def quick_test():
    print("=" * 60)
    print("QUICK WEBSOCKET PROGRESS TEST")
    print("=" * 60)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"\nSession ID: {session_id}")
    
    # Find test PDF
    test_pdf = "docs/attention-is-all-you-need.pdf"
    if not Path(test_pdf).exists():
        print(f"[ERROR] Test PDF not found: {test_pdf}")
        return False
    
    print(f"Test PDF: {test_pdf}")
    print("\nConnecting WebSocket...")
    
    try:
        uri = f"{WS_URL}/api/ws/{session_id}"
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("[OK] WebSocket connected")
            
            # Get connection message
            msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(msg)
            print(f"[OK] Connection message: {data['type']}")
            
            # Start upload in background
            print("\nUploading file...")
            loop = asyncio.get_event_loop()
            
            def upload_file():
                with open(test_pdf, 'rb') as f:
                    files = {'file': (Path(test_pdf).name, f, 'application/pdf')}
                    data = {'session_id': session_id}
                    response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
                    return response.status_code == 200
            
            upload_task = loop.run_in_executor(None, upload_file)
            
            # Monitor progress
            print("\nMonitoring progress updates:")
            print("-" * 60)
            
            progress_count = 0
            stages_seen = set()
            
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(msg)
                    
                    if data.get('type') == 'progress':
                        progress_count += 1
                        stage = data.get('stage', 'unknown')
                        progress = data.get('progress', 0)
                        message = data.get('message', '')
                        stages_seen.add(stage)
                        
                        print(f"[{progress_count}] {stage}: {progress}% - {message}")
                        
                        if data.get('status') == 'completed':
                            print("-" * 60)
                            print("[SUCCESS] Processing completed!")
                            break
                            
                except asyncio.TimeoutError:
                    # Check if upload finished
                    if upload_task.done():
                        upload_success = upload_task.result()
                        if upload_success and progress_count == 0:
                            print("[WARNING] Upload succeeded but NO progress updates!")
                            return False
                        elif not upload_success:
                            print("[ERROR] Upload failed!")
                            return False
                        else:
                            # Upload done, waiting for final progress
                            continue
                    else:
                        print("[WAIT] Still processing...")
                        continue
                except Exception as e:
                    print(f"[ERROR] {e}")
                    break
            
            print(f"\nResults:")
            print(f"  Progress updates received: {progress_count}")
            print(f"  Stages seen: {sorted(stages_seen)}")
            
            if progress_count > 0 and 'completed' in stages_seen:
                print("\n[SUCCESS] All tests passed!")
                return True
            else:
                print("\n[FAIL] Test incomplete")
                return False
                
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(quick_test())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[CANCELLED]")
        exit(1)
