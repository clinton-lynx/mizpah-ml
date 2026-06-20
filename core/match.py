from .enroll import decode_base64_image, generate_embedding
from .config import supabase

# Euclidean distance threshold for OpenCV SFace
# SFace L2 distance threshold is ~1.128, but we relax it to 1.4 for varying webcam quality
MATCH_THRESHOLD = 1.4 

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
        return {"matched": False, "confidence": 0.0, "profile": None}
        
    best_match = results[0]
    
    # Convert Euclidean distance to realistic confidence percentage
    distance = best_match['distance']
    
    if distance <= 1.128:
        # 0.0 distance = 100%, 1.128 distance = 70%
        confidence_val = 100.0 - (30.0 * (distance / 1.128))
    else:
        # 1.128 distance = 70%, 1.4 distance = 0%
        confidence_val = 70.0 * max(0.0, (1.4 - distance) / (1.4 - 1.128))
        
    confidence = round(confidence_val, 1)
    
    return {
        "matched": True,
        "confidence": confidence,
        "profile": {
            "name": best_match['name'],
            "type": best_match['type'],
            "blood_type": best_match.get('blood_type'),
            "allergies": best_match.get('allergies', []),
            "conditions": best_match.get('conditions', []),
            "emergency_contact": best_match.get('emergency_contact')
        }
    }
