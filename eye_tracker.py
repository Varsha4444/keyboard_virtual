import cv2
import mediapipe as mp
import numpy as np

class EyeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)

    def detect_gaze(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        direction = "CENTER"
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, _ = frame.shape
                left_eye_indices = [33, 133]
                right_eye_indices = [362, 263]
                nose_tip = 1

                left_eye_pts = np.array([[face_landmarks.landmark[i].x * w,
                                          face_landmarks.landmark[i].y * h] for i in left_eye_indices])
                right_eye_pts = np.array([[face_landmarks.landmark[i].x * w,
                                           face_landmarks.landmark[i].y * h] for i in right_eye_indices])
                left_center = np.mean(left_eye_pts, axis=0)
                right_center = np.mean(right_eye_pts, axis=0)
                face_center_x = (left_center[0] + right_center[0]) / 2
                nose_x = face_landmarks.landmark[nose_tip].x * w
                offset = nose_x - face_center_x

                if offset > 15:
                    direction = "LEFT"
                elif offset < -15:
                    direction = "RIGHT"

        return direction, frame, offset

