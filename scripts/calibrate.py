import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.match import match_person

def calibrate_threshold():
    """
    Tests various images against the database to find the optimal 
    confidence threshold (minimizing false positives and negatives).
    """
    print("Threshold Calibration Tool")
    print("--------------------------")
    print("Ensure you have seeded the database first!")
    print("We will test images and show you the confidence scores.")
    print("Adjust the MATCH_THRESHOLD in core/match.py based on these results.\n")
    
    test_dir = os.path.join(os.path.dirname(__file__), "test_images")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"Created {test_dir}. Place test images here to calibrate.")
        return
        
    images = os.listdir(test_dir)
    if not images:
        print(f"No images found in {test_dir}. Add some images to test.")
        return
        
    for img_name in images:
        img_path = os.path.join(test_dir, img_name)
        with open(img_path, "rb") as img_file:
            import base64
            b64 = base64.b64encode(img_file.read()).decode('utf-8')
            
        print(f"Testing {img_name}...")
        # Test against all modes to see what hits
        for mode in ["medical", "watchlist", "missing"]:
            try:
                res = match_person(b64, mode)
                if res["matched"]:
                    print(f"  -> MATCHED as {res['profile']['name']} ({mode}) | distance: {res['distance']:.4f}, confidence: {res['confidence']}%")
            except Exception as e:
                print(f"  -> Error testing {mode}: {e}")
                
if __name__ == "__main__":
    calibrate_threshold()
