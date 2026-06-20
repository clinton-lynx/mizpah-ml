import os
import sys
import cv2
import numpy as np

# Load models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'models')
YUNET_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")

if not os.path.exists(YUNET_PATH) or not os.path.exists(SFACE_PATH):
    print("Error: Model files not found in core/models/")
    sys.exit(1)

detector = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320))
recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")

def get_embedding(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Could not load image: {img_path}")
        
    height, width, _ = img.shape
    detector.setInputSize((width, height))
    
    faces = detector.detect(img)
    if faces[1] is None:
        raise ValueError(f"No face detected in {img_path}")
        
    face = faces[1][0]
    aligned_face = recognizer.alignCrop(img, face)
    feature = recognizer.feature(aligned_face)
    return feature

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test SFace distance between two images")
    parser.add_argument("image1", help="Path to first image (e.g. enrolled image)")
    parser.add_argument("image2", help="Path to second image (e.g. scanned image)")
    args = parser.parse_args()

    try:
        emb1 = get_embedding(args.image1)
        emb2 = get_embedding(args.image2)
    except ValueError as e:
        print(str(e))
        return

    # Calculate L2 Distance
    distance = recognizer.match(emb1, emb2, cv2.FaceRecognizerSF_FR_NORM_L2)
    print(f"\n[Raw L2 Distance]: {distance:.4f}")

    # Exact confidence math from core/match.py
    if distance <= 0.6:
        confidence_val = 100.0 - (10.0 * (distance / 0.6))
    elif distance <= 0.9:
        confidence_val = 90.0 - (20.0 * ((distance - 0.6) / 0.3))
    else:
        confidence_val = 70.0 - (20.0 * ((distance - 0.9) / 0.22))
        
    confidence_val = max(0.0, min(100.0, confidence_val))
    confidence = round(confidence_val, 1)
    
    print(f"[Final Confidence Score]: {confidence}%\n")
    
    if confidence > 0:
        print("Verdict: MATCH FOUND!")
    else:
        print("Verdict: NO MATCH")

if __name__ == "__main__":
    main()
