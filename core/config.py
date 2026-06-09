import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Initialize supabase client if credentials are provided
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("WARNING: Supabase credentials not found. DB actions will fail.")

# Set DeepFace configurations
DEEPFACE_MODEL = "Facenet512" # Reliable and outputs 512-d embeddings
DEEPFACE_METRIC = "cosine"
