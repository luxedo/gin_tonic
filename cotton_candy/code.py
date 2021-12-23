"""CircuitPython Essentials NeoPixel example"""
import random
import time
import board
from micropython import const
import npfirefly
from adafruit_circuitplayground import cp


# NeoPixels configuration
PIXEL_PIN = board.A1  # Adafruit Gemma M0
NUM_PIXELS = 70  # Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels
BRIGHTNESS_VALUES = [0, 0.01, 0.1, 0.5, 1.0]
BRIGHTNESS_INITIAL_IDX = 3
MIN_STEPS = 4  # Minimum firefly flicker timesteps
MAX_STEPS = 16  # Maximum firefly flicker timesteps
MAX_COLOR_DELTA = 200  # Maximum color difference

# Microphone levels
LEVEL_OFSET = 50
LEVEL_SENSIBILITY = 1 / 20
DEBOUNCE_TIMEOUT = 0.2

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


def sample_countdown():
    for i in range(len(cp.pixels)):
        cp.pixels[i] = (0, 0, 0)
    for i in range(len(cp.pixels)):
        cp.pixels[i] = (127, 127, 127)
        now = time.monotonic()
        while time.monotonic() < now + 1:
            if cp.button_a or cp.button_b:
                return


def sample_color(samples, color):
    for i in range(len(cp.pixels)):
        cp.pixels[i] = color
    acc = 0
    for _ in range(samples):
        acc += cp.light
    for i in range(len(cp.pixels)):
        cp.pixels[i] = (0, 0, 0)
    return acc / samples


def sample_colors():
    sample_countdown()
    samples = 100
    red = sample_color(samples, RED)
    green = sample_color(samples, GREEN)
    blue = sample_color(samples, BLUE)
    lowest = min([red, green, blue])
    highest = max([red, green, blue])
    delta = highest - lowest
    return (
        int((red - lowest) / delta * 255),
        int((green - lowest) / delta * 255),
        int((blue - lowest) / delta * 255),
    )


def randomize_range(red, green, blue):
    red_min = bound_color(red - int(MAX_COLOR_DELTA * random.random()))
    red_max = bound_color(red + int(MAX_COLOR_DELTA * random.random()))
    green_min = bound_color(green - int(MAX_COLOR_DELTA * random.random()))
    green_max = bound_color(green + int(MAX_COLOR_DELTA * random.random()))
    blue_min = bound_color(blue - int(MAX_COLOR_DELTA * random.random()))
    blue_max = bound_color(blue + int(MAX_COLOR_DELTA * random.random()))
    return (red_min, red_max), (green_min, green_max), (blue_min, blue_max)


def bound_color(color):
    return 0 if color < 0 else 255 if color > 255 else color


def main():
    brightness_idx = BRIGHTNESS_INITIAL_IDX
    with npfirefly.NeoPixelFirefly(
        pin=PIXEL_PIN,
        n=NUM_PIXELS,
        min_steps=MIN_STEPS,
        max_steps=MAX_STEPS,
        extra_neopixels=[cp.pixels],
    ) as fireflies:
        brightness_idx = BRIGHTNESS_INITIAL_IDX
        cp.pixels.brightness = BRIGHTNESS_VALUES[brightness_idx]
        fireflies.neopixels.brightness = BRIGHTNESS_VALUES[brightness_idx]
        cp.red_led = False
        debounce = time.monotonic()
        while True:
            red, green, blue = sample_colors()
            red_range, green_range, blue_range = randomize_range(red, green, blue)

            fireflies.red_range = red_range
            fireflies.green_range = green_range
            fireflies.blue_range = blue_range
            countdown = (random.random() + 1) * 10000
            for _ in range(countdown):
                # Reads sensor
                if cp.button_a:
                    break
                elif cp.button_b:
                    t = time.monotonic()
                    if t - debounce > DEBOUNCE_TIMEOUT:
                        debounce = t
                        brightness_idx = (brightness_idx + 1) % len(BRIGHTNESS_VALUES)
                        fireflies.neopixels.brightness = BRIGHTNESS_VALUES[
                            brightness_idx
                        ]
                        cp.pixels.brightness = BRIGHTNESS_VALUES[brightness_idx]

                for _ in range(int((cp.sound_level - LEVEL_OFSET) * LEVEL_SENSIBILITY)):
                    fireflies.flicker(final_color=(0, 0, 0))
                fireflies.update()
                fireflies.show()


if __name__ == "__main__":
    main()
