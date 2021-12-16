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
import digitalio
from nprainbow import NeoPixelRainbow


# NEOPIXEL CONSTANTS
PIXEL_PIN = board.GP18  # Neopixel pin
NUM_PIXELS = 300  # Number of NeoPixels

# NEOPIXEL INITIAL CONFIGURATION
SPEED = 1.0  # Transition speed
NUM_COLORS = 4096  # Number of colors in the table
COLOR_DELTA = 0.3  # Hue delta (begining of the strip <=> end of the strip)
COLOR_DELTA = 1.0  # Hue delta (begining of the strip <=> end of the strip)
INITIAL_HUE = 0.0  # Hue offset for the initial color

# CONFIGURATION RANGES
BRIGHTNESS_STEPS = (0, 0.01, 0.03, 0.1, 0.30, 1.0)
BRIGHTNESS_INITIAL_STEP = 3
SPEED_RANGE = (-64, 64)
NUM_COLORS_RANGE = (1, 4096)
COLOR_DELTA_RANGE = (-16, 16)
HUE_RANGE = (0, 0.5)

# Super users only
SIGMOID_A = 3  # Hue bias parameter a
SIGMOID_B = 5  # Hue bias parameter b

# BUTTONS CONFIGURATION
BTN1_PIN = board.GP7  # Neopixel pin
BTN2_PIN = board.GP11  # Neopixel pin
FEEDBACK_COLOR = (63, 63, 63)
BTN_DEBOUNCE = 0.2
POT1_PIN = board.A0
POT2_PIN = board.A2

# Peripherals
class ClickButton:
    def __init__(self, pin, debounce=0):
        self.button = digitalio.DigitalInOut(pin)
        self.button.direction = digitalio.Direction.INPUT
        self.button.pull = digitalio.Pull.DOWN
        self.pin = pin
        self.debounce = debounce
        self.timeout = time.monotonic() + self.debounce

    @property
    def pressed(self):
        now = time.monotonic()
        if self.button.value and now > self.timeout:
            self.timeout = now + self.debounce
            return True
        return False


class Potentiometer:
    change_threshold = 800
    _min_value = 9000
    _max_value = 64000

    def __init__(
        self, analog_in, initial_value, value_range, callback, profile="linear"
    ):
        self.analog_in = analog_in
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
        self.locked = True
        self.locked_value = self.bisection(
            lambda x: self.transform(x) - initial_value, 0, 1e8, 1000, 100
        )
        self._previous_value = self.locked_value
        self._value = self.analog_in.value

    def has_changed(self):
        self._value = self.analog_in.value
        if self.locked:
            val_diff = abs(self.locked_value - self._value)
            if val_diff < 5 * self.change_threshold:
                self.locked = False
                return True
        else:
            val_diff = abs(self._previous_value - self._value)
            if val_diff > self.change_threshold:
                self._previous_value = self._value
                return True
        return False

    @property
    def value(self):
        value = self.transform(self._value)
        if value < self.min_value:
            return self.min_value
        elif value > self.max_value:
            return self.max_value
        return value

    def transform(self, value):
        return (
            self._profile((value - self._min_value) / self._delta) * self.delta
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

    @staticmethod
    def bisection(f, a, b, epsilon, N):
        """
        https://personal.math.ubc.ca/~pwalls/math-python/roots-optimization/bisection/
        Approximate solution of f(x)=0 on interval [a,b] by bisection method.

        Parameters
        ----------
        f : function
            The function for which we are trying to approximate a solution f(x)=0.
        a,b : numbers
            The interval in which to search for a solution. The function returns
            None if f(a)*f(b) >= 0 since a solution is not guaranteed.
        N : (positive) integer
            The number of iterations to implement.

        Returns
        -------
        x_N : number
            The midpoint of the Nth interval computed by the bisection method. The
            initial interval [a_0,b_0] is given by [a,b]. If f(m_n) == 0 for some
            midpoint m_n = (a_n + b_n)/2, then the function returns this solution.
            If all signs of values f(a_n), f(b_n) and f(m_n) are the same at any
            iteration, the bisection method fails and return None.

        Examples
        --------
        >>> f = lambda x: x**2 - x - 1
        >>> bisection(f,1,2,25)
        1.618033990263939
        >>> f = lambda x: (2*x - 1)*(x - 3)
        >>> bisection(f,0,1,10)
        0.5
        """
        if f(a) * f(b) >= 0:
            return None
        a_n = a
        b_n = b
        for n in range(1, N + 1):
            m_n = (a_n + b_n) / 2
            f_m_n = f(m_n)
            if f(a_n) * f_m_n < 0:
                a_n = a_n
                b_n = m_n
            elif f(b_n) * f_m_n < 0:
                a_n = m_n
                b_n = b_n
            elif abs(f_m_n) < epsilon:
                return m_n
            else:
                return None
        return (a_n + b_n) / 2


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
        hue_range=HUE_RANGE,
        speed=SPEED,
        steps=NUM_COLORS,
        hue_fn=lambda x: locked_sigmoid(x, SIGMOID_A, SIGMOID_B),
        auto_write=False,
    )
    btn1 = ClickButton(BTN1_PIN, BTN_DEBOUNCE)
    btn2 = ClickButton(BTN2_PIN, BTN_DEBOUNCE)

    pot1 = analogio.AnalogIn(POT1_PIN)
    pot2 = analogio.AnalogIn(POT2_PIN)

    pot_speed = Potentiometer(
        pot1,
        SPEED,
        SPEED_RANGE,
        callback=lambda value: setattr(pixels, "speed", value),
        profile="symmetric_fifth",
    )
    pot_color_delta = Potentiometer(
        pot2,
        COLOR_DELTA,
        COLOR_DELTA_RANGE,
        callback=lambda value: setattr(pixels, "color_delta", value),
        profile="symmetric_cubic",
    )
    pot_hue_lower = Potentiometer(
        pot1,
        0,
        (0, 1),
        callback=lambda value: setattr(
            pixels,
            "hue_range",
            (value, pixels.hue_range[1]),
        ),
        profile="linear",
    )
    pot_hue_delta = Potentiometer(
        pot2,
        1,
        (0, 1),
        callback=lambda value: setattr(
            pixels, "hue_range", (pixels.hue_range[0], value)
        ),
        profile="linear",
    )

    mode_sequence = PotSequence(
        [
            [pot_hue_lower, pot_hue_delta],
            [pot_speed, pot_color_delta],
        ]
    )

    # Mainloop
    brightness_idx = BRIGHTNESS_INITIAL_STEP
    pixels.brightness = BRIGHTNESS_STEPS[brightness_idx]
    while True:
        if btn1.pressed:
            button_feedback(pixels)
            brightness_idx = (brightness_idx + 1) % len(BRIGHTNESS_STEPS)
            pixels.brightness = BRIGHTNESS_STEPS[brightness_idx]
        if btn2.pressed:
            button_feedback(pixels)
            mode_sequence.next()
        mode_sequence.update_mode()
        pixels.update()
        pixels.show()


if __name__ == "__main__":
    main()
