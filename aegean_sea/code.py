"""
# Aegean_sea

> A colorful odyssey through the rainbow.

Configuration is made with the global variables:

Examples:
```python
# BRIGHTNESS
BRIGHTNESS = 0.01  # Very Dim
BRIGHTNESS = 0.1   # Weak
BRIGHTNESS = 0.5   # Medium
BRIGHTNESS = 1.0   # MY EYES!

# SPEED
SPEED = 0    # LEDs wont change
SPEED = 0.2  # Very Slow transition
SPEED = 1    # Slow transition
SPEED = 5    # Medium transition
SPEED = 25   # Fast transition
SPEED = -25  # Fast transition (reverse direction)
SPEED = 125  # Crazy party mode

# NUM_COLORS
NUM_COLORS = 8     # Few colors
NUM_COLORS = 2^12  # True Color (tm)

# COLOR_DELTA
COLOR_DELTA = 0     # All LEDs have the same color
COLOR_DELTA = 0.5   # Half rainbow
COLOR_DELTA = -0.5  # Reversed Half rainbow
COLOR_DELTA = 1.0   # FULL rainbow
COLOR_DELTA = 2.0   # DOUBLE RAINBOOOOOOW

# INITIAL_HUE
INITIAL_HUE=0     # Starts at RED
INITIAL_HUE=0.25  # Starts at ORANGE
INITIAL_HUE=0.40  # Starts at YELLOW
INITIAL_HUE=0.50  # Starts at GREEN
INITIAL_HUE=0.60  # Starts at CYAN
INITIAL_HUE=0.7   # Starts at BLUE
INITIAL_HUE=0.8   # Starts at PURPLE
INITIAL_HUE=0.9   # Starts at PINK
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
import time
import touchio
from nprainbow import NeoPixelRainbow

# NEOPIXEL CONFIGURATION
PIXEL_PIN = board.GP28  # Neopixel pin
NUM_PIXELS = 300  # Number of NeoPixels
BRIGHTNESS = 0.10  # Pixels brightness
SPEED = 1  # Transition speed
NUM_COLORS = 2 ** 12  # Number of colors in the table
COLOR_DELTA = 0.4  # Hue delta (begining of the strip <=> end of the strip)
INITIAL_HUE = 0.0  # Hue offset for the initial color

# Super users only
SIGMOID_A = 3  # Hue bias parameter a
SIGMOID_B = 5  # Hue bias parameter b

# BUTTONS CONFIGURATION
BTN1_PIN = board.A0  # Neopixel pin
BTN_DEBOUNCE = 200
FEEDBACK_COLOR = (63, 63, 63)

# MODES CONFIGURATION
class Mode:
    def __init__(self, pixels):
        self.pixels = pixels
        self.state = {}

    def store(self):
        self.state["brightness"] = self.pixels.brightness
        self.state["speed"] = self.pixels.speed
        self.state["color_delta"] = self.pixels.color_delta
        self.state["steps"] = self.pixels.steps

    def run(self):  # Abstract Method
        raise NotImplemented("Please implement me!")


class MovingRainbow(Mode):
    def run(self):
        self.pixels.speed = self.state["speed"]


class FrozenRainbow(Mode):
    def run(self):
        self.pixels.speed = 0


class ModeSequence:
    def __init__(self, pixels, modes_list):
        self.pixels = pixels
        self.mode_idx = 0
        self.modes = [mode(pixels) for mode in modes_list]

    @property
    def mode(self):
        return self.modes[self.mode_idx]

    def next(self):
        self.mode.store()
        self.mode_idx = (self.mode_idx + 1) % len(self.modes)
        self.mode.run()


# Peripherals
class TouchButton:
    def __init__(self, pin, debounce=0):
        self.button = touchio.TouchIn(pin)
        self.button.threshold = 4000
        self.pin = pin
        self.debounce = debounce
        self.timeout = time.time()

    @property
    def pressed(self):
        if self.button.value != 0 and time.time() > self.timeout:
            self.timeout = time.time()
            return True
        return False


# Functions
def locked_sigmoid(x, a, b):
    """
    Sigmoid function that is locked to (0, 0) and (1, 1).
    """
    k = (1 + math.exp(a)) * (1 + math.exp(a - b)) / (math.exp(a) - math.exp(a - b))
    C = -k / (1 + math.exp(a))
    return k / (1 + (math.exp(a - b * x))) + C


def button_feedback(pixels):
    """
    Feedback when pressing the button
    """
    for i in range(len(pixels)):
        pixels[i] = FEEDBACK_COLOR
    pixels.show()


# Sweet main
def main():
    pixels = NeoPixelRainbow(
        PIXEL_PIN,
        NUM_PIXELS,
        color_delta=COLOR_DELTA,
        initial_hue=INITIAL_HUE,
        speed=SPEED,
        steps=NUM_COLORS,
        hue_fn=lambda x: locked_sigmoid(x, SIGMOID_A, SIGMOID_B),
        auto_write=False,
        brightness=BRIGHTNESS,
    )
    btn1 = TouchButton(BTN1_PIN, BTN_DEBOUNCE)
    mode_sequence = ModeSequence(pixels, [MovingRainbow, FrozenRainbow])
    while True:
        if btn1.pressed:
            mode_sequence.next()
            button_feedback(pixels)
        pixels.update()
        pixels.show()


if __name__ == "__main__":
    main()
