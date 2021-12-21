"""CircuitPython Essentials NeoPixel example"""
import math
import random
import time
import board
from micropython import const
import npfirefly
from adafruit_circuitplayground import cp


# NeoPixels configuration
PIXEL_PIN = board.A1  # Adafruit Gemma M0
NUM_PIXELS = 50  # Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels
BRIGHTNESS = 0.1
MIN_STEPS = 2  # Minimum firefly flicker timesteps
MAX_STEPS = 8  # Maximum firefly flicker timesteps
MAX_COLOR_DELTA = 100  # Maximum color difference


def sample_color(samples, color):
    for i in range(len(cp.pixels)):
        cp.pixels[i] = color
    acc = 0
    for _ in range(samples):
        acc += cp.light
    for i in range(len(cp.pixels)):
        cp.pixels[i] = (0, 0, 0)
    return acc / samples


def softmax(red, green, blue):
    exp_red = math.exp(red)
    exp_green = math.exp(green)
    exp_blue = math.exp(blue)
    exp_sum = exp_red + exp_green + exp_blue
    return exp_red / exp_sum, exp_green / exp_sum, exp_blue / exp_sum


def sample_countdown():
    for i in range(len(cp.pixels)):
        cp.pixels[i] = (0, 0, 0)
    for i in range(len(cp.pixels)):
        cp.pixels[i] = (127, 127, 127)
        now = time.monotonic()
        while time.monotonic() < now + 1:
            if cp.button_a or cp.button_b:
                return


def sample_colors():
    sample_countdown()
    samples = 100
    red = sample_color(samples, (255, 0, 0))
    green = sample_color(samples, (0, 255, 0))
    blue = sample_color(samples, (0, 0, 255))
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
    color = 0 if color < 0 else color
    color = 255 if color > 255 else color
    return color


def main():
    cp.pixels.brightness = BRIGHTNESS
    cp.red_led = False
    cp.green_led = False
    with npfirefly.NeoPixelFirefly(
        pin=PIXEL_PIN,
        n=NUM_PIXELS,
        brightness=BRIGHTNESS,
        min_steps=MIN_STEPS,
        max_steps=MAX_STEPS,
        # extra_neopixels=[cp.pixels],
    ) as fireflies:
        while True:
            red, green, blue = sample_colors()
            red_range, green_range, blue_range = randomize_range(red, green, blue)

            fireflies.red_range = red_range
            fireflies.green_range = green_range
            fireflies.blue_range = blue_range
            countdown = random.random() * 10000
            for _ in range(countdown):
                # Reads sensor
                if cp.button_a or cp.button_b:
                    break
                for _ in range(int(cp.sound_level / 20)):
                    fireflies.flicker(final_color=(0, 0, 0))
                fireflies.update()


if __name__ == "__main__":
    main()
