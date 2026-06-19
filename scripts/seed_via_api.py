import os
import sys
import base64
import uuid
import requests

# Add parent dir to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import supabase

# API endpoint
API_URL = "https://mizpah-ml.onrender.com/enroll"

# Fake demo data to enroll (one from each category)
DEMO_PROFILES = [
    {"name": "John Doe", "type": "watchlist", "image": "watchlist_1.jpg"},
    {"name": "Little Timmy", "type": "missing", "image": "missing_1.jpg"},
    {"name": "Alice Wonderland", "type": "medical", "blood_type": "O-", "allergies": ["Penicillin"], "conditions": ["Asthma"], "emergency_contact": "555-0101", "image": "medical_1.jpg"}
]

DEMO_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "demo_images")

def image_to_base64(filepath: str) -> str:
    with open(filepath, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def seed_database():
    if not supabase:
        print("Error: Supabase is not configured.")
        return
        
    print("Starting API-based Remote Seeding...")
    if not os.path.exists(DEMO_IMAGES_DIR):
        print(f"Error: {DEMO_IMAGES_DIR} directory does not exist.")
        return

    success_count = 0
    for profile in DEMO_PROFILES:
        img_path = os.path.join(DEMO_IMAGES_DIR, profile["image"])
        if not os.path.exists(img_path):
            print(f"Skipping {profile['name']} - Missing image {profile['image']}")
            continue
            
        print(f"Enrolling {profile['name']} ({profile['type']}) via API...")
        try:
            person_id = str(uuid.uuid4())
            b64_image = image_to_base64(img_path)
            
            # Call the production backend to generate embedding and push to DB
            payload = {
                "image": b64_image,
                "person_id": person_id,
                "type": profile["type"]
            }
            
            response = requests.post(API_URL, json=payload, timeout=60)
            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}: {response.text}")
                
            res_data = response.json()
            if not res_data.get("success"):
                raise Exception(f"API enrollment failed: {res_data.get('message')}")
                
            print(f"  ✓ API Enrollment Success: {res_data.get('embedding_id')}")
            
            # Now update the extra fields on the created row in Supabase
            extra_data = {
                "name": profile["name"],
                "blood_type": profile.get("blood_type"),
                "allergies": profile.get("allergies"),
                "conditions": profile.get("conditions"),
                "emergency_contact": profile.get("emergency_contact")
            }
            supabase.table("face_vectors").update(extra_data).eq("person_id", person_id).execute()
            print(f"  ✓ Database profile fields updated")
            
            success_count += 1
        except Exception as e:
            print(f"  X Failed: {e}")
            
    print(f"Remote seeding complete! Enrolled {success_count}/3 profiles.")

if __name__ == "__main__":
    seed_database()
