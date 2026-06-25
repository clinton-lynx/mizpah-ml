from .enroll import decode_base64_image, generate_embedding
from .config import supabase

# Euclidean distance threshold for OpenCV SFace
# SFace L2 distance standard threshold is ~1.128. We relax it to 1.5 to make webcam matching more forgiving.
MATCH_THRESHOLD = 1.5

# Defines a non-linear mapping from distance to confidence. This allows for more granular control
# over how distance impacts the confidence score. The relationship is often not linear;
# for example, a small distance change at low values (e.g., 0.1 to 0.3) might be a huge
# confidence drop, while a change from 1.2 to 1.4 is less significant.
# Each tuple is (distance_upper_bound, confidence_at_that_bound).
# The map is interpolated between these points and implicitly starts at (0.0, 100.0).
CONFIDENCE_MAP = [
    (0.9, 80.0),        # Excellent match range: 0.0-0.9 -> 100%-80%
    (1.4, 50.0),        # Good match range: 0.9-1.4 -> 80%-50%
    (MATCH_THRESHOLD, 0.0) # Marginal match range: 1.4-1.9 -> 50%-0%
]

def match_person(image_b64: str, mode: str) -> dict:
    """
    Generates embedding and queries Supabase pgvector for the closest match.
    mode determines which database/type to search.
    """
    if supabase is None:
        raise Exception("Supabase client is not configured.")
        
    try:
        img = decode_base64_image(image_b64)
        if img is None:
            raise ValueError("Corrupt or invalid image data.")
        embedding = generate_embedding(img)
    except (ValueError, AttributeError, Exception):
        return {"matched": False, "confidence": 0.0, "distance": None, "profile": None}

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
    
    distance = best_match['distance']

    # Calculate confidence using the configurable, piecewise linear map.
    # This provides more control than a simple linear conversion.
    prev_dist = 0.0
    prev_conf = 100.0
    confidence_val = 0.0 # Default to 0 if distance is beyond the threshold

    for current_dist, current_conf in CONFIDENCE_MAP:
        if distance <= current_dist:
            # The distance falls into the segment [prev_dist, current_dist].
            # We can now perform a linear interpolation for this segment.
            dist_range = current_dist - prev_dist
            conf_range = prev_conf - current_conf
            
            dist_in_segment = distance - prev_dist
            
            if dist_range > 0:
                confidence_val = prev_conf - (dist_in_segment / dist_range) * conf_range
            else: # Avoid division by zero, just use the current point's confidence
                confidence_val = current_conf
            
            break # Found our segment, so we can stop.
        
        prev_dist = current_dist
        prev_conf = current_conf

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
