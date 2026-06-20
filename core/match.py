from .enroll import decode_base64_image, generate_embedding
from .config import supabase

# Euclidean distance threshold for OpenCV SFace
# SFace L2 distance standard threshold is ~1.128. We set it to 1.12 for tight, reliable matches.
MATCH_THRESHOLD = 1.12

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
    
    # Confidence mapping adjusted for tighter 1.12 threshold
    # 0.0 to 0.6 is an excellent match (100% to 90%)
    # 0.6 to 0.9 is a good match (90% to 70%)
    # 0.9 to 1.12 is a marginal match (70% to 50%)
    distance = best_match['distance']
    if distance <= 0.6:
        confidence_val = 100.0 - (10.0 * (distance / 0.6))
    elif distance <= 0.9:
        confidence_val = 90.0 - (20.0 * ((distance - 0.6) / 0.3))
    else:
        confidence_val = 70.0 - (20.0 * ((distance - 0.9) / 0.22))
        
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
