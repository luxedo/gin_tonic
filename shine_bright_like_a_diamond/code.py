"""CircuitPython Essentials NeoPixel example"""
import time
import random
import board
import npfirefly
import adafruit_dotstar
from analogio import AnalogIn

# Vibration sensor configuration
SENSOR_WINDOW = 64  # Moving average window
SENSOR_MEAN_MIN_DEV_PERC = 0.09  # Mean minimum deviation in percent value
SENSOR_BASELINE_OUTLIERS = 0.2  # Baseline measure
SENSOR_SENSIBILITY = 0.2  # Sensor sensibility

# NeoPixels configuration
PIXEL_PIN = board.A1  # Adafruit Gemma M0
NUM_PIXELS = 50  # Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels
BRIGHTNESS = 1.0
MIN_STEPS = 8  # Minimum firefly flicker timesteps
MAX_STEPS = 64  # Maximum firefly flicker timesteps
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
        self._read = [self.sensor.value] * window_size
        self._outliers = 0

    def read(self):
        """
        Makes another read
        """
        self._read.pop(0)
        self._read.append(self.sensor.value)

    @property
    def outliers(self):
        """
        Returns the number of outliers currently in the window
        """
        self.window_counter = 1
        mean = sum(self._read) / self.window_size
        mean_min_dev = mean + mean * self.mean_min_dev_perc
        self._outliers = len([r for r in self._read if r > mean_min_dev])
        return self._outliers


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
            adafruit_dotstar.DotStar(
                board.APA102_SCK, board.APA102_MOSI, 1, auto_write=True
            )
        ],
    ) as fireflies:
        while True:
            vibration_sensor.read()
            outliers = vibration_sensor.outliers
            outliers = outliers if outliers > 0 else SENSOR_BASELINE_OUTLIERS

            # Start a random firefly
            if random.random() < outliers / SENSOR_WINDOW / SENSOR_SENSIBILITY:
                fireflies.max_steps = round(
                    MAX_STEPS * ((outliers / SENSOR_WINDOW * 2 + 1))
                )
                fireflies.flicker(final_color=(0, 0, 0))
            fireflies.update()


if __name__ == "__main__":
    main()
