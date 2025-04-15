import requests
import sys
import os

# Print clear header
print("\n" + "="*50)
print("HUGGING FACE API TEST")
print("="*50)

# Get API key from parameter or use the one in the file
API_KEY = sys.argv[1] if len(sys.argv) > 1 else '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'

# Print API key info
print(f"Using API key: {API_KEY[:5]}...{API_KEY[-4:]} (middle part hidden)")

try:
    print("\nSending test request...")
    # Try with a simple, small model
    response = requests.post(
        'https://api-inference.huggingface.co/models/gpt2',
        json={
            'inputs': 'Hello, I need help with tournament planning.'
        },
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        },
        timeout=10
    )
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("\n[SUCCESS] API CONNECTION SUCCESSFUL!\n")
        print(f"Response: {response.json()}")
    else:
        print("\n[FAILED] API CONNECTION FAILED!\n")
        print(f"Error: {response.text}")
        
except Exception as e:
    print("\n[ERROR] EXCEPTION OCCURRED!\n")
    print(f"Error: {str(e)}")

print("\n" + "="*50)
print("TEST COMPLETED")
print("="*50 + "\n")

# Keep console window open on Windows
input("\nPress Enter to exit...") 