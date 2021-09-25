"""CircuitPython Essentials NeoPixel example"""
import random
import board
from adafruit_dotstar import DotStar
from analogio import AnalogIn
from micropython import const
import npfirefly


# Vibration sensor configuration
SENSOR_WINDOW = 16  # Moving average window
SENSOR_MEAN_MIN_DEV_PERC = 0.06  # Mean minimum deviation in percent value
SENSOR_MIN_OUTLIERS = 5  # Baseline measure
SENSOR_MIN_FLICKER = 0.01  # Sensor minimum flicker

# NeoPixels configuration
PIXEL_PIN = board.A1  # Adafruit Gemma M0
NUM_PIXELS = 50  # Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels
BRIGHTNESS = 1.0
MIN_STEPS = 8  # Minimum firefly flicker timesteps
MAX_STEPS = 32  # Maximum firefly flicker timesteps
RED_RANGE = (127, 255)  # Red random color range
GREEN_RANGE = (15, 63)  # Green random color range
BLUE_RANGE = (0, 7)  # Blue random color range


class VibrationOutliers:
    """
    Measures the sensor at `port` with the `update` method and returns
    the number of detected outliers (values above `mean_dev` percent of
    the mean.
    """

    def __init__(self, port, window_size, mean_min_dev_perc=0.1):
        self.port = port
        self.window_size = window_size
        self.mean_min_dev_perc = mean_min_dev_perc
        self.sensor = AnalogIn(port)
        w = 8  # Baseline window multiplier
        self.read_batch(w * self.window_size)  # Warmup
        mean = sum(self.read_batch(w * self.window_size)) / (self.window_size * w)
        self.threshold = mean + mean * self.mean_min_dev_perc
        self._read = [0] * window_size

    def read_batch(self, n):
        """
        Returns several reads
        """
        return [self.sensor.value for _ in range(n)]

    def read(self):
        """
        Makes another read
        """
        value = self.sensor.value > self.threshold
        self._read.pop(0)
        self._read.append(value)
        return value

    @property
    def outliers(self):
        """
        Returns the number of outliers currently in the window
        """
        return sum(self._read)


def main():
    vibration_sensor = VibrationOutliers(
        board.A2, SENSOR_WINDOW, SENSOR_MEAN_MIN_DEV_PERC
    )
    with npfirefly.NeoPixelFirefly(
        pin=board.A1,
        n=NUM_PIXELS,
        brightness=BRIGHTNESS,
        min_steps=MIN_STEPS,
        max_steps=MAX_STEPS,
        red_range=RED_RANGE,
        green_range=GREEN_RANGE,
        blue_range=BLUE_RANGE,
        extra_neopixels=[
            # Board LED
            DotStar(board.APA102_SCK, board.APA102_MOSI, 1, auto_write=True)
        ],
    ) as fireflies:
        while True:
            # Reads sensor
            vibration_sensor.read()
            new_fireflies = (vibration_sensor.outliers - SENSOR_MIN_OUTLIERS) / const(
                (SENSOR_WINDOW - SENSOR_MIN_OUTLIERS)
            )
            if new_fireflies > 0 or random.random() < SENSOR_MIN_FLICKER:
                fireflies.max_steps = round(
                    MAX_STEPS * (abs(new_fireflies) * SENSOR_MIN_OUTLIERS + 1)
                )
                # Start a random firefly
                fireflies.flicker(final_color=(0, 0, 0))
                if new_fireflies > 0.5:
                    for i in range(SENSOR_WINDOW):
                        fireflies.flicker(final_color=(0, 0, 0))
            fireflies.update()


if __name__ == "__main__":
    main()
