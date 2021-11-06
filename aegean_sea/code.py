"""
# Aegean_sea

> A colorful odyssey through the rainbow.

Configuration is made with the global variables:

Examples:
```python
# SPEED
SPEED = 0   # LEDs wont change
SPEED = 0.1 # Slow transition
SPEED = 1   # Medium transition
SPEED = 10  # Fast transition
SPEED = 100 # Crazy party mode

# COLOR_DELTA
COLOR_DELTA = 0   # All LEDs have the same color
COLOR_DELTA = 0.5   # Half rainbow
COLOR_DELTA = 1.0   # FULL rainbow
COLOR_DELTA = 2.0   # DOUBLE RAINBOOOOOOW

# INITIAL_HUE
INITIAL_HUE=0  # Starts at RED
INITIAL_HUE=0.25  # Starts at ORANGE
INITIAL_HUE=0.40  # Starts at YELLOW
INITIAL_HUE=0.50  # Starts at GREEN
INITIAL_HUE=0.60  # Starts at CYAN
INITIAL_HUE=0.7  # Starts at BLUE
INITIAL_HUE=0.8  # Starts at PURPLE
INITIAL_HUE=0.9  # Starts at PINK
```

Because the LEDs response is not linear, the HUE is resampled with
a sigmoid curve bounded at (0, 0) and (1, 1) to bias the colors.
The parameter `a` shifts the curve towards red or blue. The paarameter
`b` indicates the growth of the curve.
Some examples:
a = 0.5; b = 1  # Linear
a = 3  ; b = 4  # Biased toward red
a = 1  ; b = 4  # Biased toward blue
"""
import board
import math
from nprainbow import NeoPixelRainbow

PIXEL_PIN = board.D1  # Neopixel pin
NUM_PIXELS = 20  # Number of NeoPixels
BRIGHTNESS = 0.1  # Pixels brightness
SPEED = 0.1  # Transition speed
COLOR_DELTA = 0.3  # Hue delta (begining of the strip <=> end of the strip)
INITIAL_HUE = 0.0  # Hue offset for the initial color

# Super users only
SIGMOID_A = 5  # Hue bias parameter a
SIGMOID_B = 8  # Hue bias parameter b


def locked_sigmoid(x, a, b):
    """
    Sigmoid function that is locked to (0, 0) and (1, 1).
    """
    k = (1 + math.exp(a)) * (1 + math.exp(a - b)) / (math.exp(a) - math.exp(a - b))
    C = -k / (1 + math.exp(a))
    return k / (1 + (math.exp(a - b * x))) + C


def main():
    pixels = NeoPixelRainbow(
        PIXEL_PIN,
        NUM_PIXELS,
        color_delta=COLOR_DELTA,
        initial_hue=INITIAL_HUE,
        speed=SPEED,
        hue_fn=lambda x: locked_sigmoid(x, SIGMOID_A, SIGMOID_B),
        auto_write=False,
        brightness=BRIGHTNESS,
    )
    while True:
        pixels.update()
        pixels.show()


if __name__ == "__main__":
    main()
