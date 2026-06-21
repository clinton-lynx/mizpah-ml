"""
Generates a clean JSON payload file from an image, ready to paste into Postman.
Usage: python scripts/generate_postman_body.py <image_path> [mode]
Output: Creates a .json file next to the image that you can copy-paste into Postman.
"""
import sys
import os
import base64
import json

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_postman_body.py <image_path> [mode]")
        print("Example: python scripts/generate_postman_body.py scripts/IMG_2769.JPG passive")
        sys.exit(1)

    image_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "passive"

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    # Read and encode the image as a single, clean base64 string (no line breaks)
    with open(image_path, "rb") as f:
        b64_string = base64.b64encode(f.read()).decode("utf-8")

    # Build the JSON payload
    payload = {
        "image": b64_string,
        "mode": mode
    }

    # Write to a file
    output_path = os.path.splitext(image_path)[0] + "_scan_payload.json"
    with open(output_path, "w") as f:
        json.dump(payload, f)

    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"[OK] Payload generated: {output_path} ({file_size_kb:.0f} KB)")
    print(f"   Base64 length: {len(b64_string)} chars")
    print(f"   Mode: {mode}")
    print()
    print("How to use in Postman:")
    print("  1. Open the file in a text editor")
    print("  2. Select All (Ctrl+A) and Copy (Ctrl+C)")
    print("  3. In Postman, go to Body -> raw -> JSON")
    print("  4. Clear the body and Paste (Ctrl+V)")
    print("  5. Hit Send")

if __name__ == "__main__":
    main()
