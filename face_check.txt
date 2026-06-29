import face_recognition
import cv2
import os
import time
import json
from PIL import Image
import numpy as np

# Define classroom and camera
classrooms = [
    {"room": "CSE-A", "camera_index": 0}
]

def load_known_faces():
    known_encodings = []
    known_names = []

    for filename in os.listdir("known_faces"):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join("known_faces", filename)
            try:
                pil_image = Image.open(image_path).convert("RGB")
                image = np.array(pil_image)

                if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                    print(f"[ERROR] Invalid image format: {filename}")
                    continue

                encodings = face_recognition.face_encodings(image)
                if not encodings:
                    print(f"[WARNING] No face found in {filename}")
                    continue

                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(filename)[0])
            except Exception as e:
                print(f"[ERROR] Failed to process {filename}: {e}")
                continue

    print(f"[INFO] Loaded {len(known_encodings)} known face(s)")
    return known_encodings, known_names

def update_status_file(room_name, faculty_name):
    try:
        with open("status.json", "r") as f:
            status_data = json.load(f)
    except FileNotFoundError:
        status_data = []

    # Update only the specified classroom
    updated = False
    for entry in status_data:
        if entry["room"] == room_name:
            entry["faculty"] = faculty_name
            entry["status"] = "Present" if faculty_name else "Absent"
            updated = True
            break

    if not updated:
        status_data.append({
            "room": room_name,
            "faculty": faculty_name,
            "status": "Present" if faculty_name else "Absent"
        })

    with open("status.json", "w") as f:
        json.dump(status_data, f, indent=4)

def check_faces():
    known_encodings, known_names = load_known_faces()

    for classroom in classrooms:
        room_name = classroom["room"]
        cam_index = classroom["camera_index"]

        cam = cv2.VideoCapture(cam_index)
        ret, frame = cam.read()
        cam.release()

        if not ret:
            print(f"[ERROR] Could not access camera {cam_index}")
            update_status_file(room_name, "")
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        matched_name = ""
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            if True in matches:
                matched_index = matches.index(True)
                matched_name = known_names[matched_index]
                break

        if matched_name:
            print(f"[INFO] {matched_name} detected in {room_name}")
        else:
            print(f"[INFO] No known faculty in {room_name}")

        update_status_file(room_name, matched_name)

if __name__ == "__main__":
    while True:
        print("[INFO] Checking classroom for faculty presence...")
        check_faces()
        print("[INFO] Waiting 30 seconds before next check...\n")
        time.sleep(30)