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

        # ---------------- APP MODE ----------------
        self.app_mode = "CALIBRATION"   # CALIBRATION → READY → TYPING

        # ---------------- UI ----------------
        self.title = QLabel("START CALIBRATION")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 18, QFont.Bold))

        self.text_buffer = QLabel("")
        self.text_buffer.setFont(QFont("Arial", 22))
        self.text_buffer.setStyleSheet(
            "background:#f5f5f5; padding:15px; border:2px solid black;"
        )
        self.text_buffer.setFixedHeight(90)
        self.text_buffer.hide()

        self.video = QLabel()
        self.video.setFixedSize(900, 550)
        self.video.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setFixedHeight(25)

        # Buttons
        self.start_typing_btn = QPushButton("START TYPING")
        self.clear_btn = QPushButton("CLEAR")
        self.speak_btn = QPushButton("SPEAK TEXT")
        self.exit_btn = QPushButton("EXIT")

        self.start_typing_btn.hide()
        self.clear_btn.hide()
        self.speak_btn.hide()

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_typing_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addWidget(self.speak_btn)
        btn_row.addWidget(self.exit_btn)

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
        self.keyboard.hide()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.text_buffer)
        layout.addWidget(self.video)
        layout.addWidget(self.progress)
        layout.addLayout(btn_row)
        layout.addWidget(self.keyboard)
        self.setLayout(layout)

        # ---------------- CV ----------------
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

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

        # ---------------- CALIBRATION ----------------
        self.calib_points = ["CENTER", "TL", "TR", "BL", "BR"]
        self.calib_step = 0
        self.calib_start = None
        self.center_ratio = None
        self.CALIB_DWELL = 1.5

        # ---------------- TYPING ----------------
        self.zone = "CENTER"
        self.scan_index = 0
        self.last_scan = time.time()
        self.dwell_start = None
        self.locked_key = None

        self.DWELL_TIME = 0.6
        self.SCAN_SPEED = 0.45

        # ---------------- ACTIONS ----------------
        self.start_typing_btn.clicked.connect(self.start_typing)
        self.clear_btn.clicked.connect(lambda: self.text_buffer.setText(""))
        self.speak_btn.clicked.connect(lambda: self.speak_async(self.text_buffer.text()))
        self.exit_btn.clicked.connect(self.close)

    # -------------------------------------------------
    def iris_ratio(self, lm, w):
        left = lm[33].x * w
        right = lm[133].x * w
        iris = np.mean([lm[i].x * w for i in [468, 469, 470, 471]])
        return (iris - left) / (right - left)

    def draw_dot(self, frame, point, active):
        h, w, _ = frame.shape
        pos = {
            "CENTER": (w // 2, h // 2),
            "TL": (80, 80),
            "TR": (w - 80, 80),
            "BL": (80, h - 80),
            "BR": (w - 80, h - 80)
        }
        color = (0, 0, 255) if active else (255, 0, 0)
        cv2.circle(frame, pos[point], 20, color, -1)

    # -------------------------------------------------
    def start_typing(self):
        self.app_mode = "TYPING"
        self.title.setText("Eye Gaze Virtual Keyboard")
        self.keyboard.show()
        self.text_buffer.show()
        self.clear_btn.show()
        self.speak_btn.show()
        self.start_typing_btn.hide()

    # -------------------------------------------------
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)

        if not res.multi_face_landmarks:
            self.show_frame(frame)
            return

        lm = res.multi_face_landmarks[0].landmark
        ratio = self.iris_ratio(lm, frame.shape[1])

        # ---------------- CALIBRATION ----------------
        if self.app_mode == "CALIBRATION":
            point = self.calib_points[self.calib_step]

            if self.calib_start is None:
                self.calib_start = time.time()

            dwell = time.time() - self.calib_start
            self.progress.setValue(int(min(dwell / self.CALIB_DWELL, 1) * 100))

            active = dwell >= self.CALIB_DWELL
            self.draw_dot(frame, point, active)

            if active:
                if point == "CENTER":
                    self.center_ratio = ratio
                self.calib_step += 1
                self.calib_start = None
                self.progress.setValue(0)

                if self.calib_step >= len(self.calib_points):
                    self.app_mode = "READY"
                    self.title.setText("Calibration Finished ✅")
                    self.start_typing_btn.show()

            self.show_frame(frame)
            return

        # ---------------- TYPING ----------------
        if self.app_mode == "TYPING":
            if ratio < self.center_ratio - 0.06:
                self.zone = "LEFT"
            elif ratio > self.center_ratio + 0.06:
                self.zone = "RIGHT"
            else:
                self.zone = "CENTER"

            now = time.time()
            if self.locked_key is None and self.zone in ["LEFT", "RIGHT"] and now - self.last_scan > self.SCAN_SPEED:
                self.scan_index += 1
                self.last_scan = now

            active_key = None
            for i, btn in enumerate(self.keys):
                btn.setStyleSheet("")
                if self.zone == "LEFT" and i < 14 and i == self.scan_index % 14:
                    btn.setStyleSheet("background:yellow")
                    active_key = btn
                elif self.zone == "RIGHT" and i >= 14 and (i - 14) == self.scan_index % 14:
                    btn.setStyleSheet("background:yellow")
                    active_key = btn

            if active_key:
                if self.locked_key is None:
                    self.locked_key = active_key
                    self.dwell_start = time.time()

                dwell = time.time() - self.dwell_start
                self.progress.setValue(int(min(dwell / self.DWELL_TIME, 1) * 100))

                if dwell >= self.DWELL_TIME:
                    txt = active_key.text()
                    self.text_buffer.setText(self.text_buffer.text() + (" " if txt == "␣" else txt))
                    self.speak_async("space" if txt == "␣" else txt)

                    self.locked_key = None
                    self.dwell_start = None
                    self.progress.setValue(0)
                    self.scan_index += 1
            else:
                self.locked_key = None
                self.dwell_start = None
                self.progress.setValue(0)

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
