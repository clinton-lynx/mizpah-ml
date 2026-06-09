import os
import sys
import base64
import uuid

# Add parent dir to path so we can import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.enroll import enroll_person
from core.config import supabase

# Fake demo data
DEMO_PROFILES = [
    {"name": "John Doe", "type": "watchlist", "image": "watchlist_1.jpg"},
    {"name": "Jane Smith", "type": "watchlist", "image": "watchlist_2.jpg"},
    {"name": "Robert Black", "type": "watchlist", "image": "watchlist_3.jpg"},
    
    {"name": "Little Timmy", "type": "missing", "image": "missing_1.jpg"},
    {"name": "Grandpa Joe", "type": "missing", "image": "missing_2.jpg"},
    {"name": "Sarah Connor", "type": "missing", "image": "missing_3.jpg"},
    
    {"name": "Alice Wonderland", "type": "medical", "blood_type": "O-", "allergies": ["Penicillin"], "conditions": ["Asthma"], "emergency_contact": "555-0101", "image": "medical_1.jpg"},
    {"name": "Bob Builder", "type": "medical", "blood_type": "A+", "allergies": [], "conditions": ["Diabetes Type 1"], "emergency_contact": "555-0102", "image": "medical_2.jpg"},
    {"name": "Charlie Chaplin", "type": "medical", "blood_type": "AB+", "allergies": ["Peanuts"], "conditions": [], "emergency_contact": "555-0103", "image": "medical_3.jpg"},
    {"name": "Diana Prince", "type": "medical", "blood_type": "B-", "allergies": [], "conditions": ["Epilepsy"], "emergency_contact": "555-0104", "image": "medical_4.jpg"}
]

DEMO_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "demo_images")

def image_to_base64(filepath: str) -> str:
    with open(filepath, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def seed_database():
    if not supabase:
        print("Error: Supabase is not configured.")
        return
        
    print("Starting Demo Seeding...")
    if not os.path.exists(DEMO_IMAGES_DIR):
        os.makedirs(DEMO_IMAGES_DIR)
        print(f"Created {DEMO_IMAGES_DIR}. Please place the 10 demo images there and run again.")
        return

    success_count = 0
    for profile in DEMO_PROFILES:
        img_path = os.path.join(DEMO_IMAGES_DIR, profile["image"])
        if not os.path.exists(img_path):
            print(f"Skipping {profile['name']} - Missing image {profile['image']}")
            continue
            
        print(f"Enrolling {profile['name']} ({profile['type']})...")
        try:
            person_id = str(uuid.uuid4())
            b64_image = image_to_base64(img_path)
            
            # Use the core enroll logic to generate embedding and push to DB
            enroll_person(b64_image, person_id, profile["type"])
            
            # NOTE: Joshua's schema has more fields (name, blood_type, etc). 
            # Our ML core enroll_person only saves person_id and embedding.
            # So we also need to update that row with the extra profile data
            extra_data = {
                "name": profile["name"],
                "blood_type": profile.get("blood_type"),
                "allergies": profile.get("allergies"),
                "conditions": profile.get("conditions"),
                "emergency_contact": profile.get("emergency_contact")
            }
            supabase.table("face_vectors").update(extra_data).eq("person_id", person_id).execute()
            
            success_count += 1
            print(f"  ✓ Success")
        except Exception as e:
            print(f"  X Failed: {e}")
            
    print(f"Seeding complete! Enrolled {success_count}/10 profiles.")

if __name__ == "__main__":
    seed_database()
