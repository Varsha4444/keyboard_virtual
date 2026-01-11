from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout

class KeyboardUI(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.keys = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        positions = [(i, j) for i in range(3) for j in range(9)]
        for pos, key in zip(positions, self.keys):
            btn = QPushButton(key)
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.layout.addWidget(btn, *pos)

        self.setLayout(self.layout)

    def highlight_keys(self, direction):
        for i in range(self.layout.count()):
            button = self.layout.itemAt(i).widget()
            if direction == "LEFT" and i < 13:
                button.setStyleSheet("background-color: lightgreen; font-size: 16px; font-weight: bold;")
            elif direction == "RIGHT" and i > 13:
                button.setStyleSheet("background-color: lightgreen; font-size: 16px; font-weight: bold;")
            else:
                button.setStyleSheet("font-size: 16px; font-weight: bold; background-color: none;")
