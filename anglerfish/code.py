"""CircuitPython Essentials NeoPixel example"""
import time
import random
import board
from adafruit_dotstar import DotStar
from analogio import AnalogIn
from micropython import const
import npfirefly

FIREFLIES_PROBABILITY = 0.2
FIREFLIES_MAX_AMMOUNT = 5
FIREFLIES_MAX_STEPS = 64

# NeoPixels configuration
PIXEL_PIN = board.D1  # Adafruit Gemma M0
NUM_PIXELS = 20  # Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels
BRIGHTNESS = 1.0
MIN_STEPS = 8  # Minimum firefly flicker timesteps
MAX_STEPS = 16  # Maximum firefly flicker timesteps
RED_RANGE = (0, 63)  # Red random color range
GREEN_RANGE = (0, 63)  # Green random color range
BLUE_RANGE = (63, 255)  # Blue random color range
FINAL_COLOR = (0, 0, 4)


def test_pixels(fireflies):
    while True:
        for i in range(len(fireflies)):
            fireflies[i] = (13, 0, 0)
        fireflies.show()
        time.sleep(1)
        for i in range(len(fireflies)):
            fireflies[i] = (0, 13, 0)
        fireflies.show()
        time.sleep(1)
        for i in range(len(fireflies)):
            fireflies[i] = (0, 0, 13)
        fireflies.show()
        time.sleep(1)


def main():
    with npfirefly.NeoPixelFirefly(
        pin=PIXEL_PIN,
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
        # test_pixels(fireflies)
        while True:
            if random.random() < FIREFLIES_PROBABILITY:
                color = random.random()
                if color < 1 / 3:
                    fireflies.red_range = (0, 0)
                    fireflies.green_range = (0, 0)
                if color < 2 / 3:
                    fireflies.red_range = (0, 0)
                    fireflies.green_range = (63, 195)
                else:
                    fireflies.red_range = (63, 195)
                    fireflies.green_range = (0, 0)
                new_fireflies = int(random.random() * FIREFLIES_MAX_AMMOUNT + 0.5)
                max_steps = MIN_STEPS + int(random.random() * FIREFLIES_MAX_STEPS)
                fireflies.max_steps = max_steps
                # Start a random firefly
                for _ in range(new_fireflies):
                    fireflies.flicker(final_color=FINAL_COLOR)
            fireflies.update()
            fireflies.show()


if __name__ == "__main__":
    main()
