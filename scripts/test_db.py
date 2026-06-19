import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import supabase

def test():
    if not supabase:
        print("Supabase is not configured.")
        return
    try:
        res = supabase.table("face_vectors").select("count", count="exact").limit(1).execute()
        print("Supabase connection successful. Row count:", res)
    except Exception as e:
        print("Supabase connection failed:", e)

if __name__ == "__main__":
    test()
