import cv2
import mediapipe as mp

# Initialize face detection
mp_face = mp.solutions.face_detection
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)  # open your webcam
face = mp_face.FaceDetection()

print("✅ Webcam test started! Press 'q' to quit.\n")

while True:
    success, img = cap.read()
    if not success:
        print("❌ Could not read from camera")
        break

    # Detect faces
    results = face.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    # Draw detections
    if results.detections:
        for id, detection in enumerate(results.detections):
            mp_draw.draw_detection(img, detection)

    cv2.imshow("Camera Test - Press q to exit", img)

    # Quit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Test complete, camera closed.")
