"""
# Aegean_sea

> A colorful odyssey through the rainbow.

Configuration is made with the global variables:

Examples:
```python
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
NUM_PIXELS = 77  # Number of NeoPixels
MAX_CURRENT = 2.5  # Power source max current
LED_MAX_CURRENT = 0.02  # 20 mA LED max current

# NEOPIXEL INITIAL CONFIGURATION
SPEED = 0.1  # Transition speed
NUM_COLORS = 200  # Number of colors in the table
COLOR_DELTA = 0.3  # Hue delta (begining of the strip <=> end of the strip)
HUE_LOWER = 0.0  # Hue offset initial color
HUE_UPPER = 1.0  # Hue offset final color
BRIGHTNESS = 0.2  # Initial brightness
SATURATION = 1.0  # Initial saturation

# CONFIGURATION RANGES
SPEED_RANGE = (-64, 64)
COLOR_DELTA_RANGE = (-16, 16)
UNIT_RANGE = (0, 1.0)
MAX_BRIGHTNESS = MAX_CURRENT / NUM_PIXELS / LED_MAX_CURRENT
MAX_BRIGHTNESS = 1 if MAX_BRIGHTNESS > 1 else MAX_BRIGHTNESS
MAX_BRIGHTNESS = 0.01 if MAX_BRIGHTNESS <= 0 else MAX_BRIGHTNESS
BRIGHTNESS_RANGE = (0, MAX_BRIGHTNESS)

# Super users only
SIGMOID_A = 3  # Hue bias parameter a
SIGMOID_B = 5  # Hue bias parameter b

# BUTTONS CONFIGURATION
BTN1_PIN = board.GP11  # Mode button
BTN2_PIN = board.GP7  # On/Off/Reset button
POT1_PIN = board.A0
POT2_PIN = board.A2

# Peripherals
class ClickButton:
    PRESSED = "PRESSED"
    RELEASED = "RELEASED"

    def __init__(
        self,
        pin,
        press_callback=lambda: None,
        release_callback=lambda: None,
        hold_callback=lambda: None,
        hold_callback_timeout=1,
    ):
        self.button = digitalio.DigitalInOut(pin)
        self.button.direction = digitalio.Direction.INPUT
        self.button.pull = digitalio.Pull.DOWN
        self.pin = pin
        self._value = self.button.value
        self._previous_value = self.button.value
        self.press_callback = press_callback
        self.release_callback = release_callback
        self.hold_callback = hold_callback
        self.hold_callback_timeout = hold_callback_timeout
        self.skip_release = False
        self.holding = False
        self.holding_tick = 0

    def update(self):
        self._previous_value = self._value
        self._value = self.button.value
        if self._previous_value != self._value:
            if self._value:
                self.press_callback()
                self.holding = True
                self.holding_tick = time.monotonic()
            else:
                if self.skip_release:
                    self.skip_release = False
                    return
                self.release_callback()
                self.holding = False
        else:
            if (
                self.holding
                and time.monotonic() - self.holding_tick > self.hold_callback_timeout
            ):
                self.hold_callback()
                self.holding = False
                self.skip_release = True


class Potentiometer:
    change_threshold = 400
    _min_value = 2000
    _max_value = 64000
    window_size = 20

    def __init__(
        self, analog_in, initial_value, value_range, callback, profile="linear"
    ):
        self.analog_in = analog_in
        self.initial_value = initial_value
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
        self.window = [self.analog_in.value for _ in range(self.window_size)]
        self.lock(self.initial_value)

    def has_changed(self):
        if self.locked:
            val_diff = abs(self.locked_value - self.analog_in.value)
            if val_diff < 10 * self.change_threshold:
                self.unlock()
                return True
        else:
            self.window.pop(0)
            self.window.append(self.analog_in.value)
            self._value = sum(self.window) / self.window_size
            val_diff = abs(self._previous_value - self._value)
            if val_diff > self.change_threshold:
                self._previous_value = self._value
                return True
            else:
                return False

    @property
    def value(self):
        value = self.transform(self.bound_value)
        if value < self.min_value:
            return self.min_value
        elif value > self.max_value:
            return self.max_value
        return value

    @property
    def bound_value(self):
        if self.locked:
            return self._bound_value
        bound_value = (self._value - self._min_value) / self._delta
        if bound_value < 0:
            return 0
        elif bound_value > 1:
            return 1
        return bound_value

    def transform(self, value):
        return self._profile(value) * self.delta + self.min_value

    def update(self):
        if self.has_changed():
            self.callback(self.value)
            return True
        return False

    def lock(self, value=None):
        if value is not None:
            self.locked_value = self.bisection(
                lambda x: self.transform((x - self._min_value) / self._delta) - value,
                0,
                1e8,
                1000,
                100,
            )
            self._previous_value = self.locked_value
            self._value = sum(self.window) / self.window_size
            self._bound_value = (self.locked_value - self._min_value) / self._delta
            self._bound_value = (
                0
                if self._bound_value < 0
                else 1
                if self._bound_value > 1
                else self._bound_value
            )
            self.locked = True
        else:
            if not self.locked:
                self.locked_value = self._value
                self._bound_value = self.bound_value
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
    n_colors = 64

    def __init__(self, modes, pixels, indicator_timeout=5):
        self.modes = modes
        self.current_index = 0
        self.pixels = pixels
        self.indicator_timeout = indicator_timeout
        self.all_pots = [pot for mode in self.modes for pot in mode["pots"]]
        self.n_indicators = 1 + len(self.all_pots)
        self._timeout = time.monotonic() + self.indicator_timeout
        self.color_table = NeoPixelRainbow.create_color_table(
            steps=int(
                3 * self.n_colors / 2
            ),  # Final color should be blue. Psst thiss just a trick
            saturation=1.0,
        )

    def reset(self):
        for pot in self.all_pots:
            pot.lock(pot.initial_value)
            pot.callback(pot.initial_value)

    def next(self):
        for pot in self.modes[self.current_index]["pots"]:
            pot.lock()
        self.current_index = (self.current_index + 1) % len(self.modes)
        self._timeout = time.monotonic() + self.indicator_timeout

    def update(self):
        has_changed = False
        for pot in self.modes[self.current_index]["pots"]:
            has_changed |= pot.update()
        if has_changed:
            self._timeout = time.monotonic() + self.indicator_timeout
        if self._timeout != 0:
            if time.monotonic() < self._timeout:
                self.pixels[0] = self.modes[self.current_index]["color"]
                for i, pot in enumerate(self.all_pots):
                    color_idx = math.floor((self.n_colors - 1) * pot.bound_value)
                    self.pixels[i + 1] = list(
                        self.color_table[3 * color_idx : 3 * (color_idx + 1)]
                    )
                self.pixels[self.n_indicators] = [0, 0, 0]
            else:
                self._timeout = 0


# Functions
def locked_sigmoid(x, a, b):
    """
    Sigmoid function that is locked to (0, 0) and (1, 1).
    """
    k = (1 + math.exp(a)) * (1 + math.exp(a - b)) / (math.exp(a) - math.exp(a - b))
    C = -k / (1 + math.exp(a))
    return k / (1 + (math.exp(a - b * x))) + C


# Sweet main
def main():
    pixels = NeoPixelRainbow(
        PIXEL_PIN,
        NUM_PIXELS,
        brightness=0.1,
        color_delta=COLOR_DELTA,
        initial_hue=HUE_LOWER,
        hue_range=(HUE_LOWER, HUE_UPPER),
        speed=SPEED,
        steps=NUM_COLORS,
        saturation=1.0,
        hue_fn=lambda x: locked_sigmoid(x, SIGMOID_A, SIGMOID_B),
        auto_write=False,
    )

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
        HUE_LOWER,
        UNIT_RANGE,
        callback=lambda value: setattr(
            pixels,
            "hue_range",
            (value, pixels.hue_range[1]),
        ),
        profile="linear",
    )
    pot_hue_delta = Potentiometer(
        pot2,
        HUE_UPPER,
        UNIT_RANGE,
        callback=lambda value: setattr(
            pixels, "hue_range", (pixels.hue_range[0], value)
        ),
        profile="linear",
    )
    pot_sat = Potentiometer(
        pot1,
        SATURATION,
        UNIT_RANGE,
        callback=lambda value: setattr(pixels, "saturation", value),
        profile="linear",
    )
    pot_bright = Potentiometer(
        pot2,
        BRIGHTNESS,
        BRIGHTNESS_RANGE,
        callback=lambda value: setattr(pixels, "brightness", value),
        profile="quadratic",
    )
    pot_sequence = PotSequence(
        [
            {"color": (255, 0, 0), "pots": [pot_speed, pot_color_delta]},
            {"color": (0, 255, 0), "pots": [pot_hue_lower, pot_hue_delta]},
            {"color": (0, 0, 255), "pots": [pot_sat, pot_bright]},
        ],
        pixels=pixels,
        indicator_timeout=5,
    )

    btn1 = ClickButton(
        BTN1_PIN,
        release_callback=lambda: setattr(
            pixels,
            "brightness",
            0 if pixels.brightness != 0 else pot_bright.value,
        ),
        hold_callback=lambda: pot_sequence.reset(),
        hold_callback_timeout=1,
    )
    btn2 = ClickButton(
        BTN2_PIN,
        release_callback=lambda: pot_sequence.next(),
    )

    # Mainloop
    while True:
        btn1.update()
        btn2.update()
        pixels.update()
        for i in range(5):
            pot_sequence.update()
        pixels.show()


if __name__ == "__main__":
    main()
