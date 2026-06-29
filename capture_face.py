import cv2

name = input("Enter faculty name (e.g., faculty1): ").strip()
save_path = f"known_faces/{name}.jpg"

cap = cv2.VideoCapture(0)
print("[INFO] Press SPACE to capture, ESC to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to open webcam.")
        break

    cv2.imshow("Capture Face", frame)
    key = cv2.waitKey(1)

    if key % 256 == 27:  # ESC
        print("[INFO] Escape hit, closing...")
        break
    elif key % 256 == 32:  # SPACE
        cv2.imwrite(save_path, frame)
        print(f"[INFO] Image saved to {save_path}")
        break

cap.release()
cv2.destroyAllWindows()
