from .enroll import decode_base64_image, generate_embedding
from .config import supabase

# Euclidean distance threshold for OpenCV SFace
# SFace L2 distance threshold is ~1.128, but we relax it to 1.8 for varying webcam quality
MATCH_THRESHOLD = 1.8 

def match_person(image_b64: str, mode: str) -> dict:
    """
    Generates embedding and queries Supabase pgvector for the closest match.
    mode determines which database/type to search.
    """
    if supabase is None:
        raise Exception("Supabase client is not configured.")
        
    img = decode_base64_image(image_b64)
    
    try:
        embedding = generate_embedding(img)
    except ValueError:
        return {"matched": False, "confidence": 0.0, "profile": None}

    # Format the embedding for Postgres vector search
    vector_string = f"[{','.join(map(str, embedding))}]"
    
    # Query Supabase using a Postgres RPC function 
    response = supabase.rpc(
        'match_face',
        {
            'query_embedding': vector_string,
            'match_threshold': MATCH_THRESHOLD, # Supabase now uses direct Euclidean distance
            'match_count': 1,
            'search_mode': mode
        }
    ).execute()
    
    results = response.data
    
    if not results:
        return {"matched": False, "confidence": 0.0, "distance": None, "profile": None}
        
    best_match = results[0]
    
    # Webcam-friendly confidence mapping
    # 0.0 to 0.8 is a great match (100% to 80%)
    # 0.8 to 1.5 is a decent/poor match (80% to 20%)
    # 1.5 to 1.8 is a terrible match (20% to 0%)
    distance = best_match['distance']
    if distance <= 0.8:
        confidence_val = 100.0 - (20.0 * (distance / 0.8))
    elif distance <= 1.5:
        confidence_val = 80.0 - (60.0 * ((distance - 0.8) / 0.7))
    else:
        confidence_val = 20.0 - (20.0 * ((distance - 1.5) / 0.3))
        
    confidence_val = max(0.0, min(100.0, confidence_val))
    confidence = round(confidence_val, 1)
    
    return {
        "matched": True,
        "confidence": confidence,
        "distance": round(distance, 4),
        "profile": {
            "person_id": best_match.get("person_id"),
            "name": best_match.get("name"),
            "type": best_match.get("type"),
            "blood_type": best_match.get('blood_type'),
            "allergies": best_match.get('allergies', []),
            "conditions": best_match.get('conditions', []),
            "emergency_contact": best_match.get('emergency_contact')
        }
    }
