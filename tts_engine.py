import pyttsx3
import threading

class TTSEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)
        self.engine.setProperty('volume', 0.9)

    def speak(self, text):
        if not text:
            return
        threading.Thread(target=lambda: (self.engine.say(text), self.engine.runAndWait())).start()
