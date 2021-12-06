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
import analogio
import touchio
from nprainbow import NeoPixelRainbow


# NEOPIXEL CONSTANTS
PIXEL_PIN = board.GP18  # Neopixel pin
NUM_PIXELS = 300  # Number of NeoPixels

# NEOPIXEL INITIAL CONFIGURATION
SPEED = 0.2  # Transition speed
NUM_COLORS = 4096  # Number of colors in the table
COLOR_DELTA = 0.3  # Hue delta (begining of the strip <=> end of the strip)
INITIAL_HUE = 0.0  # Hue offset for the initial color

# CONFIGURATION RANGES
BRIGHTNESS_STEPS = (0, 0.01, 0.03, 0.1, 0.30, 0.60, 1)
BRIGHTNESS_INITIAL_STEP = 3
SPEED_RANGE = (-1000, 1000)
NUM_COLORS_RANGE = (1, 4096)
COLOR_DELTA_RANGE = (-100, 100)
INITIAL_HUE_RANGE = (0, 1)

# Super users only
SIGMOID_A = 3  # Hue bias parameter a
SIGMOID_B = 5  # Hue bias parameter b

# BUTTONS CONFIGURATION
BTN1_PIN = board.A0  # Neopixel pin
BTN_DEBOUNCE = 200
FEEDBACK_COLOR = (63, 63, 63)


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


class MockAnalogIn:
    def __init__(self, pin):
        self.growing = True
        self.counter = 1000
        self.min = 1000
        self.max = 64000

    @property
    def value(self):
        if self.growing:
            self.counter += 100
            if self.counter >= self.max:
                self.growing = False
        else:
            self.counter -= 100
            if self.counter <= self.min:
                self.growing = True
        return self.counter


class Potentiometer:
    change_trheshold = 10
    _min_value = 1000
    _max_value = 64000

    def __init__(
        self, analog_in, initial_value, value_range, callback, profile="linear"
    ):
        self.analog_in = analog_in
        self.locked_value = initial_value
        self.locked = True
        self._delta = self._max_value - self._min_value
        self.min_value = value_range[0]
        self.max_value = value_range[1]
        self.delta = self.max_value - self.min_value
        self.callback = callback
        self.profile = profile
        if self.profile == "linear":
            self._profile = lambda x: x
        elif self.profile == "quadratic":
            self._profile = lambda x: x ** 2
        elif self.profile == "cubic":
            self._profile = lambda x: x ** 3
        elif self.profile == "symmetric_cubic":
            self._profile = lambda x: (((2 * x) - 1) ** 3 + 1) / 2
        elif self.profile == "symmetric_fifth":
            self._profile = lambda x: (((2 * x) - 1) ** 5 + 1) / 2
        elif self.profile == "symmetric_seventh":
            self._profile = lambda x: (((2 * x) - 1) ** 5 + 1) / 2
        else:
            raise NotImplemented(f"Profile {self.profile} not implemented")
        self._previous_value = self.analog_in.value
        self._value = self.analog_in.value

    def has_changed(self):
        self._value = self.analog_in.value
        val_diff = abs(self._previous_value - self._value)
        if self.locked:
            if val_diff < self.change_trheshold:
                self.locked = False
                return True
        elif val_diff > self.change_trheshold:
            self._previous_value = self._value
            return True
        return False

    @property
    def value(self):
        return (
            self._profile((self._value - self._min_value) / self._delta) * self.delta
            + self.min_value
        )

    def update(self):
        if self.has_changed():
            self.callback(self.value)

    def lock(self):
        self.locked_value = self._value
        self.locked = True

    def unlock(self):
        self.locked = False


class PotSequence:
    def __init__(self, modes):
        self.modes = modes
        self.current_index = 0

    def next(self):
        for pot in self.modes[self.current_index]:
            pot.lock()
        self.current_index = (self.current_index + 1) % len(self.modes)

    def update_mode(self):
        for pot in self.modes[self.current_index]:
            pot.update()


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
    )
    btn1 = TouchButton(BTN1_PIN, BTN_DEBOUNCE)

    # pot1 = analogio.AnalogIn(board.A1)
    # pot2 = analogio.AnalogIn(board.A2)
    pot1 = MockAnalogIn(board.A1)
    pot2 = MockAnalogIn(board.A2)

    def update_speed(value):
        pixels.speed = value

    def update_num_colors(value):
        pixels.steps = int(value)

    def update_color_delta(value):
        pixels.color_delta = value

    def update_initial_hue(value):
        pixels.initial_hue = value

    pot_speed = Potentiometer(
        pot1, SPEED, SPEED_RANGE, callback=update_speed, profile="symmetric_seventh"
    )
    pot_num_colors = Potentiometer(
        pot2,
        NUM_COLORS,
        NUM_COLORS_RANGE,
        callback=update_num_colors,
        profile="cubic",
    )
    pot_color_delta = Potentiometer(
        pot1,
        COLOR_DELTA,
        COLOR_DELTA_RANGE,
        callback=update_color_delta,
        profile="symmetric_seventh",
    )
    pot_initial_hue = Potentiometer(
        pot2,
        INITIAL_HUE,
        INITIAL_HUE_RANGE,
        callback=update_initial_hue,
        profile="linear",
    )

    mode_sequence = PotSequence(
        [
            [pot_speed, pot_num_colors],
            [pot_color_delta, pot_initial_hue],
        ]
    )

    # Mainloop
    brightness_idx = BRIGHTNESS_INITIAL_STEP
    pixels.brightness = BRIGHTNESS_STEPS[brightness_idx]
    while True:
        if btn1.pressed:
            button_feedback(pixels)
            mode_sequence.next()
        # if btn2.pressed:
        #     button_feedback(pixels)
        #     brightness_idx = (brightness_idx + 1) % len(BRIGHTNESS_STEPS)
        #     pixels.brightness = BRIGHTNESS_STEPS[brightness_idx]

        mode_sequence.update_mode()
        pixels.update()
        pixels.show()


if __name__ == "__main__":
    main()
