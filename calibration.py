import time
import numpy as np


class Calibration:
    def __init__(self, screen_width, screen_height, dwell_time=1.5):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.dwell_time = dwell_time

        # Calibration steps (FULL SCREEN)
        self.steps = [
            "TOP_LEFT",
            "TOP_RIGHT",
            "BOTTOM_LEFT",
            "BOTTOM_RIGHT",
            "CENTER"
        ]

        # Screen coordinates for each step
        self.screen_points = {
            "TOP_LEFT": (0, 0),
            "TOP_RIGHT": (screen_width, 0),
            "BOTTOM_LEFT": (0, screen_height),
            "BOTTOM_RIGHT": (screen_width, screen_height),
            "CENTER": (screen_width // 2, screen_height // 2),
        }

        # Storage
        self.gaze_samples = {step: [] for step in self.steps}

        self.current_step = 0
        self.start_time = None
        self.completed = False

        # Mapping coefficients
        self.coeff_x = None
        self.coeff_y = None

    # -------------------------------------------------
    def start(self):
        self.current_step = 0
        self.start_time = None
        self.completed = False
        print("\n[Calibration] Started")

    # -------------------------------------------------
    def record(self, gaze_offset):
        """
        gaze_offset: (x_offset, y_offset) from eye-gaze tracking
        Returns True when a calibration point is completed
        """

        if self.completed:
            return False

        if self.start_time is None:
            self.start_time = time.time()

        # Wait until dwell time is satisfied
        if time.time() - self.start_time < self.dwell_time:
            return False

        step = self.steps[self.current_step]
        self.gaze_samples[step].append(gaze_offset)

        print(f"[Calibration] Recorded {step}: gaze={gaze_offset}, screen={self.screen_points[step]}")

        # Move to next step
        self.current_step += 1
        self.start_time = None

        # Finish calibration
        if self.current_step >= len(self.steps):
            self.completed = True
            self.compute_mapping()
            print("[Calibration] Completed ✅")

        return True

    # -------------------------------------------------
    def compute_mapping(self):
        """
        Computes linear mapping:
        screen_x = a1 * gaze_x + b1
        screen_y = a2 * gaze_y + b2
        """

        gaze_x = []
        gaze_y = []
        screen_x = []
        screen_y = []

        for step in self.steps:
            gx, gy = np.mean(self.gaze_samples[step], axis=0)
            sx, sy = self.screen_points[step]

            gaze_x.append(gx)
            gaze_y.append(gy)
            screen_x.append(sx)
            screen_y.append(sy)

        # Linear regression (1D)
        self.coeff_x = np.polyfit(gaze_x, screen_x, 1)
        self.coeff_y = np.polyfit(gaze_y, screen_y, 1)

        print("\n[Calibration Mapping Coefficients]")
        print(f"screen_x = {self.coeff_x[0]:.4f} * gaze_x + {self.coeff_x[1]:.4f}")
        print(f"screen_y = {self.coeff_y[0]:.4f} * gaze_y + {self.coeff_y[1]:.4f}")

    # -------------------------------------------------
    def map_gaze_to_screen(self, gaze_offset):
        """
        Converts gaze offset → screen coordinate
        """
        if not self.completed:
            return None

        gx, gy = gaze_offset
        sx = self.coeff_x[0] * gx + self.coeff_x[1]
        sy = self.coeff_y[0] * gy + self.coeff_y[1]

        return int(sx), int(sy)

    # -------------------------------------------------
    def get_current_instruction(self):
        if self.completed:
            return "Calibration Completed ✅"
        return f"Look at the {self.steps[self.current_step].replace('_', ' ')} dot"
