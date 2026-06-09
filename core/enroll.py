import base64
import numpy as np
import cv2
from deepface import DeepFace
from .config import supabase, DEEPFACE_MODEL

def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decodes a base64 string into an OpenCV image array."""
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]
    
    img_data = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def generate_embedding(image: np.ndarray) -> list:
    """Extracts a face embedding using DeepFace."""
    # Enforce detection and get embedding
    objs = DeepFace.represent(img_path=image, model_name=DEEPFACE_MODEL, enforce_detection=True)
    if not objs:
        raise ValueError("No face detected in the image.")
    
    # Return the 512-d embedding of the most prominent face
    return objs[0]["embedding"]

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
