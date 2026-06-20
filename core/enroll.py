import base64
import numpy as np
import cv2
import os
from .config import supabase

# Paths to the models
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
YUNET_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")

# Initialize OpenCV models
detector = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320))
recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")

def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decodes a base64 string into an OpenCV image array."""
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]
    
    img_data = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def generate_embedding(image: np.ndarray) -> list:
    """Extracts a face embedding using native OpenCV SFace."""
    # Resize image if it's too large to prevent CPU timeout / 502 Bad Gateway
    height, width, _ = image.shape
    max_dim = 800
    if max(width, height) > max_dim:
        scale = max_dim / max(width, height)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))
        height, width, _ = image.shape
        
    detector.setInputSize((width, height))
    
    faces = detector.detect(image)
    if faces[1] is None:
        raise ValueError("No face detected in the image.")
    
    # Get the most prominent face
    face = faces[1][0]
    
    # Align and crop the face using landmarks
    aligned_face = recognizer.alignCrop(image, face)
    
    # Extract the 128-dimensional feature vector
    feature = recognizer.feature(aligned_face)
    return feature[0].tolist()

def enroll_person(image_b64: str, person_id: str, profile_type: str) -> str:
    """Generates embedding and stores it in Supabase."""
    if supabase is None:
        raise Exception("Supabase client is not configured.")
        
    img = decode_base64_image(image_b64)
    if img is None:
        raise ValueError("Corrupt or invalid image data.")
    embedding = generate_embedding(img)
    
    # Insert into supabase
    data, count = supabase.table("face_vectors").insert({
        "person_id": person_id,
        "type": profile_type,
        "embedding": embedding
    }).execute()
    
    return data[1][0]['id'] if data[1] else "inserted"
