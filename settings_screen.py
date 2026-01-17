from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QSlider, QComboBox, QCheckBox, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SettingsScreen(QWidget):
    def __init__(self, parent=None, engine=None, settings=None, callbacks=None):
        super().__init__(parent)

        self.engine = engine
        self.settings = settings or {}
        self.callbacks = callbacks or {}

        self.setFont(QFont("Arial", 12))

        # ================= SCROLL AREA =================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # ================= TITLE =================
        title = QLabel("⚙ Settings")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ================= DWELL TIME =================
        dwell_box = QGroupBox("Dwell Time (0.5s – 1.5s)")
        dwell_layout = QVBoxLayout()

        self.dwell_slider = QSlider(Qt.Horizontal)
        self.dwell_slider.setRange(5, 15)
        self.dwell_slider.setValue(int(self.settings.get("dwell_time", 0.6) * 10))

        self.dwell_value = QLabel(f"{self.dwell_slider.value() / 10:.1f} seconds")
        self.dwell_value.setAlignment(Qt.AlignCenter)

        self.dwell_slider.valueChanged.connect(
            lambda v: self.dwell_value.setText(f"{v / 10:.1f} seconds")
        )

        dwell_layout.addWidget(self.dwell_value)
        dwell_layout.addWidget(self.dwell_slider)
        dwell_box.setLayout(dwell_layout)
        layout.addWidget(dwell_box)

        # ================= SPEECH RATE =================
        rate_box = QGroupBox("Speech Rate")
        rate_layout = QVBoxLayout()

        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(100, 250)
        self.rate_slider.setValue(self.settings.get("rate", 170))

        rate_layout.addWidget(QLabel("Slow → Fast"))
        rate_layout.addWidget(self.rate_slider)
        rate_box.setLayout(rate_layout)
        layout.addWidget(rate_box)

        # ================= VOLUME =================
        volume_box = QGroupBox("Volume")
        volume_layout = QVBoxLayout()

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.settings.get("volume", 1.0) * 100))

        volume_layout.addWidget(QLabel("Mute → Loud"))
        volume_layout.addWidget(self.volume_slider)
        volume_box.setLayout(volume_layout)
        layout.addWidget(volume_box)

        # ================= VOICE =================
        voice_box = QGroupBox("Voice Selection")
        voice_layout = QVBoxLayout()

        self.voice_dropdown = QComboBox()
        self.voices = engine.getProperty("voices") if engine else []

        for i, v in enumerate(self.voices):
            self.voice_dropdown.addItem(v.name, i)

        self.voice_dropdown.setCurrentIndex(self.settings.get("voice_index", 0))
        voice_layout.addWidget(self.voice_dropdown)
        voice_box.setLayout(voice_layout)
        layout.addWidget(voice_box)

        # ================= DARK MODE =================
        self.dark_mode = QCheckBox("Enable Dark Mode")
        self.dark_mode.setChecked(self.settings.get("dark_mode", False))
        layout.addWidget(self.dark_mode)

        # ================= BUTTONS =================
        btn_row = QHBoxLayout()

        save_btn = QPushButton("SAVE")
        recalib_btn = QPushButton("RECALIBRATE")
        back_btn = QPushButton("BACK")

        save_btn.clicked.connect(self.save_settings)
        recalib_btn.clicked.connect(self.handle_recalibrate)
        back_btn.clicked.connect(self.handle_back)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(recalib_btn)
        btn_row.addWidget(back_btn)

        layout.addLayout(btn_row)

        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    # =====================================================
    # ACTIONS
    # =====================================================
    def save_settings(self):
        new_settings = {
            "dwell_time": self.dwell_slider.value() / 10,
            "rate": self.rate_slider.value(),
            "volume": self.volume_slider.value() / 100,
            "voice_index": self.voice_dropdown.currentData(),
            "dark_mode": self.dark_mode.isChecked()
        }

        if "on_save" in self.callbacks:
            self.callbacks["on_save"](new_settings)

        if "on_back" in self.callbacks:
            self.callbacks["on_back"]()

    def handle_recalibrate(self):
        if "on_recalibrate" in self.callbacks:
            self.callbacks["on_recalibrate"]()

    def handle_back(self):
        if "on_back" in self.callbacks:
            self.callbacks["on_back"]()
