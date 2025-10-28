"""Debug script to test get_run_results directly"""
import sys
sys.path.insert(0, 'C:/Users/shuta/Desktop/Smart-Trade')

from lab_runner import get_run_results
import traceback

run_id = "1a92791b-c0e2-4bff-8b4e-c47b298cb16d"

print(f"Testing get_run_results for run_id: {run_id}\n")

try:
    results = get_run_results(run_id)
    print(f"SUCCESS! Got {len(results)} trials")
    
    if results:
        print("\nFirst trial:")
        for key, value in results[0].items():
            print(f"  {key}: {value}")
    else:
        print("WARNING: No trials found (empty results)")
  
except Exception as e:
    print(f"ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
