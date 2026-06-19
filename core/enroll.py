import base64
import numpy as np
import cv2
import face_recognition
from .config import supabase

def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decodes a base64 string into an OpenCV image array."""
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]
    
    img_data = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def generate_embedding(image: np.ndarray) -> list:
    """Extracts a face embedding using dlib face_recognition."""
    # Convert BGR (OpenCV) to RGB (face_recognition)
    rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Get face encodings
    encodings = face_recognition.face_encodings(rgb_img)
    if not encodings:
        raise ValueError("No face detected in the image.")
    
    # Return the 128-d embedding of the first face
    return encodings[0].tolist()

def enroll_person(image_b64: str, person_id: str, profile_type: str) -> str:
    """Generates embedding and stores it in Supabase."""
    if supabase is None:
        raise Exception("Supabase client is not configured.")
        
    img = decode_base64_image(image_b64)
    embedding = generate_embedding(img)
    
    # Insert into supabase
    # Note: Table structure assumed based on technical spec
    data, count = supabase.table("face_vectors").insert({
        "person_id": person_id,
        "type": profile_type,
        "embedding": embedding
    }).execute()
    
    return data[1][0]['id'] if data[1] else "inserted"
