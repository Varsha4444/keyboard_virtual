import sys
import cv2
import mediapipe as mp
import numpy as np
import time
import pyttsx3
import threading

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QGridLayout, QHBoxLayout, QProgressBar
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont


class EyeGazeKeyboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Eye Gaze Virtual Keyboard")
        self.setGeometry(100, 50, 1200, 800)

        # ---------------- UI ----------------
        self.title = QLabel("Press START to calibrate")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 18, QFont.Bold))

        self.text_buffer = QLabel("")
        self.text_buffer.setFont(QFont("Arial", 22))
        self.text_buffer.setStyleSheet(
            "background:#f5f5f5; padding:15px; border:2px solid black;"
        )
        self.text_buffer.setFixedHeight(90)

        self.video = QLabel()
        self.video.setFixedSize(800, 500)
        self.video.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setFixedHeight(25)

        # Buttons
        self.start_btn = QPushButton("START")
        self.clear_btn = QPushButton("CLEAR")
        self.speak_btn = QPushButton("SPEAK TEXT")
        self.exit_btn = QPushButton("EXIT")

        btn_row = QHBoxLayout()
        for b in [self.start_btn, self.clear_btn, self.speak_btn, self.exit_btn]:
            b.setFixedHeight(40)
            btn_row.addWidget(b)

        # ---------------- KEYBOARD ----------------
        self.keyboard = QWidget()
        grid = QGridLayout()
        self.keys = []

        key_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE"]
        for i, ch in enumerate(key_chars):
            btn = QPushButton("␣" if ch == "SPACE" else ch)
            btn.setFixedSize(85, 85)
            btn.setFont(QFont("Arial", 16, QFont.Bold))
            self.keys.append(btn)
            grid.addWidget(btn, i // 9, i % 9)

        self.keyboard.setLayout(grid)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.text_buffer)
        layout.addWidget(self.video, alignment=Qt.AlignCenter)
        layout.addWidget(self.progress)
        layout.addLayout(btn_row)
        layout.addWidget(self.keyboard)
        self.setLayout(layout)

        # ---------------- CV ----------------
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

        # ---------------- TTS ----------------
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 170)

        def speak_async(text):
            threading.Thread(
                target=lambda: (self.engine.say(text), self.engine.runAndWait()),
                daemon=True
            ).start()

        self.speak_async = speak_async

        # ---------------- STATE ----------------
        self.calibrated = False
        self.center_ratio = None
        self.calib_start = None
        self.calib_step = 0
        self.calib_points = ["CENTER", "TL", "TR", "BL", "BR"]

        self.zone = "CENTER"
        self.scan_index = 0
        self.last_scan_time = time.time()

        self.dwell_start = None
        self.DWELL_TIME = 0.6      # 🔥 FAST typing
        self.SCAN_SPEED = 0.45    # 🔥 Stable scanning

        self.scanning_paused = False

        # Actions
        self.start_btn.clicked.connect(self.start_system)
        self.clear_btn.clicked.connect(lambda: self.text_buffer.setText(""))
        self.speak_btn.clicked.connect(self.speak_text)
        self.exit_btn.clicked.connect(self.close)

    # -------------------------------------------------
    def start_system(self):
        self.cap = cv2.VideoCapture(0)
        self.calibrated = False
        self.calib_step = 0
        self.center_ratio = None
        self.calib_start = time.time()
        self.timer.start(30)
        self.title.setText("Calibration started – follow the dots 👁️")

    def speak_text(self):
        if self.text_buffer.text().strip():
            self.speak_async(self.text_buffer.text())

    # -------------------------------------------------
    def iris_ratio(self, lm, w):
        left = lm[33].x * w
        right = lm[133].x * w
        iris = np.mean([lm[i].x * w for i in [468, 469, 470, 471]])
        return (iris - left) / (right - left)

    def draw_calibration_dot(self, frame, point):
        h, w, _ = frame.shape
        positions = {
            "CENTER": (w // 2, h // 2),
            "TL": (60, 60),
            "TR": (w - 60, 60),
            "BL": (60, h - 60),
            "BR": (w - 60, h - 60)
        }
        cv2.circle(frame, positions[point], 15, (0, 0, 255), -1)

    # -------------------------------------------------
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            h, w, _ = frame.shape
            ratio = self.iris_ratio(lm, w)

            # -------- CALIBRATION --------
            if not self.calibrated:
                point = self.calib_points[self.calib_step]
                self.draw_calibration_dot(frame, point)

                if time.time() - self.calib_start > 1.8:
                    if point == "CENTER":
                        self.center_ratio = ratio
                    self.calib_step += 1
                    self.calib_start = time.time()

                    if self.calib_step >= len(self.calib_points):
                        self.calibrated = True
                        self.title.setText("Calibration complete – typing enabled ✅")

                self.show_frame(frame)
                return

            # -------- ZONE --------
            if ratio < self.center_ratio - 0.06:
                self.zone = "LEFT"
            elif ratio > self.center_ratio + 0.06:
                self.zone = "RIGHT"
            else:
                self.zone = "CENTER"

            # -------- SCANNING (PAUSED DURING DWELL) --------
            now = time.time()
            if (
                not self.scanning_paused
                and self.zone in ["LEFT", "RIGHT"]
                and now - self.last_scan_time > self.SCAN_SPEED
            ):
                self.scan_index += 1
                self.last_scan_time = now
                self.dwell_start = None
                self.progress.setValue(0)

            # -------- HIGHLIGHT --------
            active_key = None
            for i, btn in enumerate(self.keys):
                btn.setStyleSheet("")
                if self.zone == "LEFT" and i < 14 and i == self.scan_index % 14:
                    btn.setStyleSheet("background:yellow")
                    active_key = btn
                elif self.zone == "RIGHT" and i >= 14 and (i - 14) == self.scan_index % 14:
                    btn.setStyleSheet("background:yellow")
                    active_key = btn

            # -------- DWELL SELECTION --------
            if active_key and self.zone in ["LEFT", "RIGHT"]:
                self.scanning_paused = True

                if self.dwell_start is None:
                    self.dwell_start = time.time()

                dwell = time.time() - self.dwell_start
                self.progress.setValue(int(min(dwell / self.DWELL_TIME, 1) * 100))

                if dwell >= self.DWELL_TIME:
                    key_text = active_key.text()
                    self.text_buffer.setText(
                        self.text_buffer.text() + (" " if key_text == "␣" else key_text)
                    )
                    self.speak_async(key_text if key_text != "␣" else "space")

                    # Reset for next key
                    self.dwell_start = None
                    self.progress.setValue(0)
                    self.scanning_paused = False
                    self.scan_index += 1
            else:
                self.scanning_paused = False
                self.progress.setValue(0)
                self.dwell_start = None

        self.show_frame(frame)

    # -------------------------------------------------
    def show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video.setPixmap(QPixmap.fromImage(img))


# =========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EyeGazeKeyboard()
    win.show()
    sys.exit(app.exec_())
