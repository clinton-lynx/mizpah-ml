import os
import sys
import base64
import requests

API_URL = "https://mizpah-ml.onrender.com/scan"
DEMO_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "demo_images")

def image_to_base64(filepath: str) -> str:
    with open(filepath, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def test_scan():
    print(f"Testing the /scan endpoint at {API_URL}...")
    
    # Test with the medical image
    img_path = os.path.join(DEMO_IMAGES_DIR, "medical_1.jpg")
    if not os.path.exists(img_path):
        print(f"Error: Could not find sample image at {img_path}")
        return

    b64_image = image_to_base64(img_path)
    
    # Payload for the scan request
    payload = {
        "image": b64_image,
        "mode": "passive" 
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=300)
        
        if response.status_code != 200:
            print(f"API Error ({response.status_code}): {response.text}")
        else:
            print("API Response:")
            print(response.json())
            
    except Exception as e:
        print(f"Failed to connect to the API: {e}")

if __name__ == "__main__":
    test_scan()
