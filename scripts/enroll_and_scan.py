"""
Enroll & Scan Demo
==================
Takes an image file, base64 encodes it, enrolls it via POST /enroll,
then scans it via POST /scan to verify the match.

Usage:
  python scripts/enroll_and_scan.py <image_path> [name] [type]

Examples:
  python scripts/enroll_and_scan.py scripts/demo_user.jpg "Clinton" medical
  python scripts/enroll_and_scan.py scripts/demo_user.jpg "Clinton" watchlist
"""
import sys
import os
import base64
import json
import uuid

# Try to use requests, fall back to urllib if not available
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USE_REQUESTS = False

# ─── CONFIG ──────────────────────────────────────────────────────
BASE_URL = os.environ.get("MIZPAH_API_URL", "https://mizpah-ml.onrender.com")
# BASE_URL = "http://localhost:8000"  # Uncomment for local testing


def encode_image(image_path: str) -> str:
    """Read an image file and return a clean base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def api_post(endpoint: str, payload: dict) -> dict:
    """POST JSON to the API and return the response."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8")

    if USE_REQUESTS:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    else:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/enroll_and_scan.py <image_path> [name] [type]")
        print()
        print("Arguments:")
        print("  image_path   Path to the face image (JPG, PNG, etc.)")
        print('  name         Person name (default: "Demo User")')
        print('  type         Profile type: medical, watchlist, missing (default: medical)')
        print()
        print("Examples:")
        print('  python scripts/enroll_and_scan.py scripts/demo_user.jpg "Clinton" medical')
        sys.exit(1)

    image_path = sys.argv[1]
    person_name = sys.argv[2] if len(sys.argv) > 2 else "Demo User"
    profile_type = sys.argv[3] if len(sys.argv) > 3 else "medical"

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"  MIZPAH ML — Enroll & Scan Demo")
    print(f"{'='*60}")
    print(f"  API:    {BASE_URL}")
    print(f"  Image:  {image_path}")
    print(f"  Name:   {person_name}")
    print(f"  Type:   {profile_type}")
    print(f"{'='*60}")
    print()

    # ─── STEP 1: Encode the image ───────────────────────────────
    print("[1/3] Encoding image to base64...")
    b64_image = encode_image(image_path)
    file_size_kb = os.path.getsize(image_path) / 1024
    b64_size_kb = len(b64_image) / 1024
    print(f"      File size:   {file_size_kb:.0f} KB")
    print(f"      Base64 size: {b64_size_kb:.0f} KB ({len(b64_image)} chars)")
    print()

    # ─── STEP 2: Enroll the face ────────────────────────────────
    person_id = str(uuid.uuid4())
    print(f"[2/3] Enrolling face...")
    print(f"      person_id: {person_id}")
    print(f"      type:      {profile_type}")
    
    enroll_payload = {
        "image": b64_image,
        "person_id": person_id,
        "type": profile_type
    }

    try:
        enroll_result = api_post("/enroll", enroll_payload)
        print(f"      [OK] Enrollment result:")
        print(f"         success:      {enroll_result.get('success')}")
        print(f"         message:      {enroll_result.get('message')}")
        print(f"         embedding_id: {enroll_result.get('embedding_id')}")
    except Exception as e:
        print(f"      [FAIL] Enrollment failed: {e}")
        print()
        print("      This might be because:")
        print("      - The Render service is cold-starting (wait 30s and retry)")
        print("      - Supabase credentials are not configured (will get mock response)")
        print("      - No face was detected in the image")
        return

    print()

    # ─── STEP 3: Scan to verify the match ───────────────────────
    # Map profile type to scan mode
    mode = "active" if profile_type == "medical" else "passive"
    
    print(f"[3/3] Scanning face to verify match...")
    print(f"      mode: {mode}")

    scan_payload = {
        "image": b64_image,
        "mode": mode
    }

    try:
        scan_result = api_post("/scan", scan_payload)
        print(f"      [OK] Scan result:")
        print(f"         matched:    {scan_result.get('matched')}")
        print(f"         confidence: {scan_result.get('confidence')}%")
        print(f"         distance:   {scan_result.get('distance')}")
        
        profile = scan_result.get("profile")
        if profile:
            print(f"         -- Profile --")
            for key, val in profile.items():
                if val is not None:
                    print(f"         {key}: {val}")
    except Exception as e:
        print(f"      [FAIL] Scan failed: {e}")

    print()
    print(f"{'='*60}")
    print("  Done! The face has been enrolled and verified.")
    print(f"{'='*60}")

    # ─── Save payloads for Postman reference ────────────────────
    output_dir = os.path.dirname(image_path) or "."
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    enroll_file = os.path.join(output_dir, f"{base_name}_enroll_payload.json")
    scan_file = os.path.join(output_dir, f"{base_name}_scan_payload.json")
    
    with open(enroll_file, "w") as f:
        json.dump(enroll_payload, f)
    with open(scan_file, "w") as f:
        json.dump(scan_payload, f)
    
    print()
    print(f"  Saved Postman payloads:")
    print(f"    Enroll: {enroll_file}")
    print(f"    Scan:   {scan_file}")


if __name__ == "__main__":
    main()
