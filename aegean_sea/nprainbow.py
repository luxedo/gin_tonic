from array import array
from neopixel import NeoPixel


class NeoPixelRainbow(NeoPixel):
    """
    Neopixel rainbow effect.

    Please check https://github.com/luxedo/gin_tonic/tree/main/aegean_sea
    for demo and examples.
    """

    steps = 256 * 2

    def __init__(
        self, *args, color_delta, initial_hue, speed, hue_fn=lambda x: x, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.color_delta = int((self.steps * color_delta) / len(self))
        self.speed = speed
        self.base_idx = 0
        self.speed_acc = 0
        self.color_table = self.create_color_table(self.steps, initial_hue, hue_fn)

    def update(self):
        """
        Please 🙏 call me at each tick to update the LEDs
        """
        idx = 0
        for i in range(len(self)):
            offset = (self.base_idx + idx) % (3 * self.steps)
            self[i] = self.color_table[offset : offset + 3]
            idx += 3 * self.color_delta
        self.speed_acc += self.speed
        if self.speed_acc >= 1:
            self.base_idx += 3 * int(self.speed_acc)
            self.base_idx %= 3 * self.steps
            self.speed_acc = 0

    def create_color_table(self, steps, initial_hue=0, hue_fn=lambda x: x):
        """
        Builds the color table with n `steps`. Hue can be biased with
        `hue_fn`. Defaults to a linear function when omitted.
        """
        table = array("B", [])
        for i in range(self.steps):
            hue = hue_fn((initial_hue + 1 / self.steps * i) % 1.0)
            for c in self.hsv_to_rgb(hue, 1, 1):
                table.append(int(255 * c))
        return table

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
