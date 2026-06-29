import cv2

img = cv2.imread("known_faces/Varshitha.jpg")
if img is None:
    print("[❌] Could not read the image.")
else:
    print("[✅] Image loaded successfully")
    print("Data type:", img.dtype)  # Should be uint8
    print("Shape:", img.shape)      # Should be (H, W, 3)