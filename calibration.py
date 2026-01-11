import time

class Calibration:
    def __init__(self):
        self.center_offset = None
        self.left_offset = None
        self.right_offset = None
        self.current_step = 0
        self.start_time = None
        self.steps = ["CENTER", "LEFT", "RIGHT"]
        self.completed = False

    def start(self):
        self.current_step = 0
        self.start_time = time.time()
        self.completed = False

    def record(self, offset):
        if self.start_time is None:
            self.start_time = time.time()
        return False
        if time.time() - self.start_time < 2:
            self.samples[self.steps[self.current_step]].append(offset)
        return False


        step = self.steps[self.current_step]

        if step == "CENTER":
            self.center_offset = offset
        elif step == "LEFT":
            self.left_offset = offset
        elif step == "RIGHT":
            self.right_offset = offset

        self.current_step += 1
        self.start_time = time.time()

        if self.current_step >= len(self.steps):
            self.completed = True

        return True

    def get_current_instruction(self):
        if self.completed:
            return "Calibration Completed ✅"
        return f"Look at the {self.steps[self.current_step]} dot"

