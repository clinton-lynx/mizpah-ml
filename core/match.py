from .enroll import decode_base64_image, generate_embedding
from .config import supabase

# Euclidean distance threshold for OpenCV SFace
# SFace L2 distance threshold is ~1.128
MATCH_THRESHOLD = 1.128 

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
    
    # Convert Euclidean distance to confidence percentage (0 distance = 100%, 1.128 distance = 0%)
    distance = best_match['distance']
    # Cap confidence between 0 and 100
    confidence_val = max(0.0, 100 * (1 - (distance / MATCH_THRESHOLD)))
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
