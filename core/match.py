from .enroll import decode_base64_image, generate_embedding
from .config import supabase

# A realistic threshold for Facenet512 cosine similarity.
# Lower means stricter. This will be calibrated later.
MATCH_THRESHOLD = 0.40 

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
    # (Joshua must create an RPC named 'match_face' in Supabase!)
    response = supabase.rpc(
        'match_face',
        {
            'query_embedding': vector_string,
            'match_threshold': 1 - MATCH_THRESHOLD, # pgvector uses distance, so similarity is 1 - distance
            'match_count': 1,
            'search_mode': mode
        }
    ).execute()
    
    results = response.data
    
    if not results:
        return {"matched": False, "confidence": 0.0, "profile": None}
        
    best_match = results[0]
    
    # Convert pgvector distance back to a confidence percentage
    similarity = 1 - best_match['similarity']
    confidence = round(similarity * 100, 1)
    
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
