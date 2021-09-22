"""CircuitPython Essentials NeoPixel example"""
import time
import math
import random
import board
import neopixel
from analogio import AnalogIn


def fade(color1, color2, steps, current_step):
    deltas = (
        (color2[0] - color1[0]) / (steps - 1),
        (color2[1] - color1[1]) / (steps - 1),
        (color2[2] - color1[2]) / (steps - 1),
    )
    return (
        math.floor(color1[0] + deltas[0] * current_step),
        math.floor(color1[1] + deltas[1] * current_step),
        math.floor(color1[2] + deltas[2] * current_step),
    )


def random_color(red_range, green_range, blue_range):
    return (
        random.randint(*red_range),
        random.randint(*green_range),
        random.randint(*blue_range),
    )


def main():
    ANALOG_WINDOW = 4
    ANALOG_SENSIBILITY = 5e-3
    ANALOG_OFFSET = -11915
    BASELINE_THRESHOLD = 0.01
    PIXEL_PIN = board.A1
    NUM_PIXELS = 50
    BRIGHTNESS = 1.0
    MIN_STEPS = 8
    MAX_STEPS = 127
    RED_RANDOM = (127, 255)
    GREEN_RANDOM = (15, 91)
    BLUE_RANDOM = (0, 7)
    NO_PALETTE = 0.001

    import adafruit_dotstar

    board_led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)
    board_led[0] = (0, 0, 0)

    with neopixel.NeoPixel(
        PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=True
    ) as pixels:
        px_states = [[-1, 0, (0, 0, 0)] for _ in pixels]
        vibration_sensor = AnalogIn(board.A2)
        threshold = 0
        analog_read = [0]
        while True:
            # Vibration sensor set threshold
            analog_read.append(vibration_sensor.value)
            if len(analog_read) == ANALOG_WINDOW:
                voltage = sum(analog_read) / ANALOG_WINDOW
                threshold = ANALOG_SENSIBILITY * (voltage + ANALOG_OFFSET)
                threshold = threshold if threshold > 0 else BASELINE_THRESHOLD
                analog_read = []

            # Create random NeoPixel
            new_pixel = random.random()
            if new_pixel < threshold:
                max_steps = random.randint(MIN_STEPS, MAX_STEPS)
                idx = random.randint(0, len(px_states) - 1)
                px_states[idx] = [
                    max_steps - 1,
                    max_steps,
                    random_color((0, 255), (0, 255), (0, 255))
                    if new_pixel < NO_PALETTE
                    else random_color(RED_RANDOM, GREEN_RANDOM, BLUE_RANDOM),
                ]

            # Render NeoPixels
            for i, st in enumerate(px_states):
                if st[0] >= 0:
                    if i == len(px_states) - 1:
                        board_led[0] = fade((0, 0, 0), st[2], st[1], st[0])
                    else:
                        pixels[i] = fade((0, 0, 0), st[2], st[1], st[0])
                    st[0] -= 1


if __name__ == "__main__":
    main()
