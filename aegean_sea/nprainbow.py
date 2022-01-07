"""
NeoPixel rainbow library
"""
from array import array
import math

from neopixel import NeoPixel


class NeoPixelRainbow(NeoPixel):
    """
    Neopixel rainbow effect.

    Please check https://github.com/luxedo/gin_tonic/tree/main/aegean_sea
    for demo and examples.
    """

    sat_levels = 20

    def __init__(
        self,
        *args,
        color_delta,
        initial_hue,
        hue_range,
        speed,
        steps,
        saturation,
        hue_fn=lambda x: x,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.hue_fn = hue_fn
        self.color_delta = color_delta
        self.initial_hue = initial_hue
        self.steps = steps
        self.saturation = saturation
        self.hue_range = hue_range
        self.speed = speed
        self.base_idx = 0
        self.speed_acc = 0
        for i in range(len(self)):
            self[i] = (0, 0, 0)
        self.show()

    @property
    def initial_hue(self):
        return self._initial_hue

    @initial_hue.setter
    def initial_hue(self, value):
        self._initial_hue = value % 1

    @property
    def steps(self):
        return self._steps

    @steps.setter
    def steps(self, value):
        self._steps = value
        self.color_tables = [
            self.create_color_table(self._steps, i / self.sat_levels, self.hue_fn)
            for i in range(self.sat_levels + 1)
        ]
        self.color_table = self.color_tables[-1]

    @property
    def saturation(self):
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._saturation = value
        self.color_table = self.color_tables[round(value * self.sat_levels)]

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = value
        speed_factor = self.sigmoid(value / 100) - 0.5
        if speed_factor < 0:
            speed_factor = 1 + speed_factor
        self._normalized_speed = speed_factor * 2 * self._hue_steps

    @property
    def hue_range(self):
        return self._hue_range

    @hue_range.setter
    def hue_range(self, value):
        self._hue_range = value
        self._hue_lower = round(value[0] * self.steps)
        self._hue_steps = round(value[1] * self.steps)
        self._hue_steps = 1 if self._hue_steps <= 0 else self._hue_steps
        self._hue_loop = self._hue_steps > 0.99 * self.steps

    def update(self):
        """
        Please 🙏 call me at each tick to update the LEDs
        """
        color_steps_delta = self._hue_steps * self.color_delta / len(self)
        if self._hue_loop:
            color_indices = [
                round((self._hue_lower + self.base_idx + i * color_steps_delta))
                % self.steps
                for i in range(len(self))
            ]
        else:
            color_indices = []
            for i in range(len(self)):
                index = round(self.base_idx + i * color_steps_delta) % (
                    2 * self._hue_steps
                )
                if index > self._hue_steps:
                    index = self._hue_steps - (index % self._hue_steps)
                index = (self._hue_lower + index) % self.steps
                color_indices.append(index)

        for i, color in enumerate(color_indices):
            self[i] = list(self.color_table[3 * color : 3 * (color + 1)])

        self.speed_acc += self._normalized_speed
        if self.speed_acc >= 1:
            self.base_idx += int(self.speed_acc)
            self.base_idx %= 2 * self._hue_steps
            self.speed_acc = 0

    @staticmethod
    def create_color_table(steps, saturation=1, hue_fn=lambda x: x):
        """
        Builds the color table with n `steps`. Hue can be biased with
        `hue_fn`. Defaults to a linear function when omitted.
        """
        table = array("B", [])
        for i in range(steps):
            hue = hue_fn(i / steps)
            for c in NeoPixelRainbow.hsv_to_rgb(hue, saturation, 1.0):
                table.append(int(255 * c))
        return table

    @staticmethod
    def sigmoid(x):
        return 1 / (1 + math.exp(-x))

    # THANK YOU COLORSYS MODULE!
    @staticmethod
    def hsv_to_rgb(h, s, v):
        if s == 0.0:
            return v, v, v
        i = int(h * 6.0)  # XXX assume int() truncates!
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        if i == 0:
            return v, t, p
        if i == 1:
            return q, v, p
        if i == 2:
            return p, v, t
        if i == 3:
            return p, q, v
        if i == 4:
            return t, p, v
        if i == 5:
            return v, p, q
        # Cannot get here
