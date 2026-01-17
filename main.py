from database_manager import (
    create_tables,
    insert_user,
    start_session,
    insert_gaze_data,
    insert_calibration_data
)


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

from settings_screen import SettingsScreen
from pro_manager import ProfileManager


class EyeGazeKeyboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Eye Gaze Virtual Keyboard")
        self.resize(1200, 800)

        # ---------------- PROFILE ----------------
        self.profile_manager = ProfileManager()
        # ---------------- DATABASE ----------------
        create_tables()
        self.user_id = insert_user("Default User", 20)
        self.session_id = start_session(self.user_id)


        # ---------------- MODE ----------------
        self.app_mode = "CALIBRATION"

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 170)
        self.engine.setProperty("volume", 1.0)

        def speak_async(text):
            if text.strip():
                threading.Thread(
                    target=lambda: (self.engine.say(text), self.engine.runAndWait()),
                    daemon=True
                ).start()

        self.speak_async = speak_async

        # ---------------- PARAMETERS ----------------
        self.DWELL_TIME = 0.6
        self.SCAN_SPEED = 0.45

        # ---------------- UI ----------------
        self.title = QLabel("Calibration started – follow the dots 👁️")
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
        self.video.setAlignment(Qt.AlignCenter)
        self.video.setMinimumSize(900, 550)

        self.progress = QProgressBar()
        self.progress.setMaximum(100)

        # ---------------- BUTTONS ----------------
        self.start_typing_btn = QPushButton("START TYPING")
        self.stop_btn = QPushButton("STOP")
        self.settings_btn = QPushButton("SETTINGS")
        self.clear_btn = QPushButton("CLEAR")
        self.speak_btn = QPushButton("SPEAK TEXT")
        self.exit_btn = QPushButton("EXIT")

        self.start_typing_btn.hide()
        self.stop_btn.hide()
        self.clear_btn.hide()
        self.speak_btn.hide()

        btn_row = QHBoxLayout()
        for b in [
            self.start_typing_btn, self.stop_btn,
            self.settings_btn, self.clear_btn,
            self.speak_btn, self.exit_btn
        ]:
            btn_row.addWidget(b)

        # ---------------- KEYBOARD ----------------
        self.keyboard = QWidget()
        grid = QGridLayout(self.keyboard)
        self.keys = []

        for i, ch in enumerate(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE"]):
            btn = QPushButton("␣" if ch == "SPACE" else ch)
            btn.setFixedSize(85, 85)
            btn.setFont(QFont("Arial", 16, QFont.Bold))
            self.keys.append(btn)
            grid.addWidget(btn, i // 9, i % 9)

        self.keyboard.hide()

        # ---------------- LAYOUT ----------------
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.text_buffer)
        self.layout.addWidget(self.video)
        self.layout.addWidget(self.progress)
        self.layout.addLayout(btn_row)
        self.layout.addWidget(self.keyboard)

        # ---------------- CV ----------------
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

        # ---------------- CALIBRATION ----------------
        self.calib_points = ["CENTER", "TL", "TR", "BL", "BR"]
        self.calib_step = 0
        self.calib_start = None
        self.center_ratio = None
        self.CALIB_DWELL = 1.5

        # ---------------- TYPING STATE ----------------
        self.zone = "CENTER"
        self.scan_index = 0
        self.last_scan = time.time()
        self.dwell_start = None
        self.locked_key = None

        # ---------------- ACTIONS ----------------
        self.start_typing_btn.clicked.connect(self.start_typing)
        self.stop_btn.clicked.connect(self.stop_typing)
        self.settings_btn.clicked.connect(self.open_settings)
        self.clear_btn.clicked.connect(lambda: self.text_buffer.setText(""))
        self.speak_btn.clicked.connect(lambda: self.speak_async(self.text_buffer.text()))
        self.exit_btn.clicked.connect(self.close)

    # =====================================================
    # SETTINGS HANDLERS (FIXED)
    # =====================================================
    def open_settings(self):
        if self.app_mode == "SETTINGS":
            return

        try:
            self.app_mode = "SETTINGS"
            self.keyboard.hide()
            self.progress.setValue(0)

            self.settings_panel = SettingsScreen(
                parent=self,                     # ✅ CRITICAL FIX
                engine=self.engine,
                settings={
                    "dwell_time": self.DWELL_TIME,
                    "rate": self.engine.getProperty("rate"),
                    "volume": self.engine.getProperty("volume"),
                    "voice_index": 0,
                    "dark_mode": False
                },
                callbacks={
                    "on_save": self.apply_settings,
                    "on_back": self.close_settings,
                    "on_recalibrate": self.restart_calibration
                }
            )

            self.layout.addWidget(self.settings_panel)
            self.settings_panel.show()

        except Exception as e:
            print("❌ SETTINGS SCREEN ERROR ❌")
            print(e)
            self.app_mode = "TYPING"
            self.keyboard.show()


    def close_settings(self):
        if hasattr(self, "settings_panel") and self.settings_panel:
            self.settings_panel.setParent(None)
            self.settings_panel.deleteLater()
            self.settings_panel = None

        self.app_mode = "TYPING"
        self.keyboard.show()


    def apply_settings(self, settings):
        self.DWELL_TIME = settings["dwell_time"]
        self.engine.setProperty("rate", settings["rate"])
        self.engine.setProperty("volume", settings["volume"])
        voices = self.engine.getProperty("voices")
        self.engine.setProperty("voice", voices[settings["voice_index"]].id)

    def restart_calibration(self):
        self.app_mode = "CALIBRATION"
        self.calib_step = 0
        self.calib_start = None
        self.center_ratio = None
        self.title.setText("Recalibration started – follow the dots 👁️")
        self.close_settings()

    # =====================================================
    # START / STOP TYPING
    # =====================================================
    def start_typing(self):
        self.app_mode = "TYPING"
        self.keyboard.show()
        self.text_buffer.show()
        self.clear_btn.show()
        self.speak_btn.show()
        self.start_typing_btn.hide()
        self.stop_btn.show()
        self.title.setText("Eye Gaze Virtual Keyboard")

    def stop_typing(self):
        self.app_mode = "PAUSED"
        self.keyboard.hide()
        self.stop_btn.hide()
        self.start_typing_btn.show()
        self.title.setText("Typing Paused")

    # =====================================================
    # FRAME LOOP
    # =====================================================
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

        if self.app_mode == "CALIBRATION":
            self.handle_calibration(frame, ratio)
        elif self.app_mode == "TYPING":
            self.handle_typing(ratio)

        self.show_frame(frame)

    # =====================================================
    # CALIBRATION
    # =====================================================
    def handle_calibration(self, frame, ratio):
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
            insert_calibration_data(
                self.user_id,
                point,
                ratio,
                0.0,
                1
            )

            self.calib_step += 1
            self.calib_start = None
            self.progress.setValue(0)

            if self.calib_step >= len(self.calib_points):
                self.app_mode = "READY"
                self.title.setText("Calibration Finished ✅")
                self.start_typing_btn.show()

    # =====================================================
    # TYPING
    # =====================================================
    def handle_typing(self, ratio):
        if ratio < self.center_ratio - 0.06:
            self.zone = "LEFT"
        elif ratio > self.center_ratio + 0.06:
            self.zone = "RIGHT"
        else:
            self.zone = "CENTER"
        insert_gaze_data(self.session_id, self.zone)

            

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
                self.text_buffer.setText(
                    self.text_buffer.text() + (" " if txt == "␣" else txt)
                )
                self.speak_async("space" if txt == "␣" else txt)

                self.locked_key = None
                self.dwell_start = None
                self.progress.setValue(0)
                self.scan_index += 1
        else:
            self.locked_key = None
            self.dwell_start = None
            self.progress.setValue(0)

    # =====================================================
    def iris_ratio(self, lm, w):
        left = lm[33].x * w
        right = lm[133].x * w
        iris = np.mean([lm[i].x * w for i in [468, 469, 470, 471]])
        return (iris - left) / (right - left)

    def draw_dot(self, frame, point, active):
        h, w, _ = frame.shape
        margin = 100
        pos = {
            "CENTER": (w // 2, h // 2),
            "TL": (margin, margin),
            "TR": (w - margin, margin),
            "BL": (margin, h - margin),
            "BR": (w - margin, h - margin)
        }
        color = (0, 0, 255) if active else (255, 0, 0)
        cv2.circle(frame, pos[point], 25, color, -1)

    def show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            self.video.width(), self.video.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video.setPixmap(pix)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EyeGazeKeyboard()
    win.show()
    sys.exit(app.exec_())
