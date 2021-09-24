import neopixel
import random


class NeoPixelFirefly(neopixel.NeoPixel):
    """
    Neopixel firefly effect. Neopixels should blink and then fade out.

    * Random time interval is chosen with `max_steps` and
    `min_steps`.
    * Random pixel color is chosen with `red_range`, `green_range`,
    `blue_range`.
    * Any extra neopixels may be added to the effect with
    `extra_neopixels` argument.

    Call `flicker` to set a pixel to flicker and then call `update`
    at each timestep to update pixel values.

    Please check https://github.com/luxedo/gin_tonic/tree/main/shine_bright_like_a_diamond
    for demo and examples.
    """

    def __init__(
        self,
        *args,
        min_steps=8,
        max_steps=256,
        red_range=(0, 255),
        green_range=(0, 255),
        blue_range=(0, 255),
        extra_neopixels=list(),
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.extra_neopixels = extra_neopixels
        for npxs in self.extra_neopixels:
            npxs.fill((0, 0, 0))
        self.lengths = [len(self)] + [len(npxs) for npxs in self.extra_neopixels]
        self.n_total = sum(self.lengths)
        self.min_steps = min_steps
        self.max_steps = max_steps
        self.red_range = red_range
        self.green_range = green_range
        self.blue_range = blue_range
        self.total_steps = [0 for i in range(self.n_total)]
        self.current_step = [-1 for i in range(self.n_total)]
        self.initial_color = [(0, 0, 0) for i in range(self.n_total)]
        self.color_deltas = [(0, 0, 0) for i in range(self.n_total)]

    def __setitem__(self, index, val):
        if index < self.n:
            super().__setitem__(index, val)
        else:
            index -= self.n
            for bank in range(len(self.extra_neopixels)):
                try:
                    self.extra_neopixels[bank].__setitem__(index, val)
                except IndexError:
                    index -= lengths[1 + bank]

    def __getitem__(self, index):
        if index < self.n:
            return super().__getitem__(index)
        else:
            return self.extra_neopixels[index - self.n]

    def flicker(self, i=None, steps=None, initial_color=None, final_color=(0, 0, 0)):
        """
        Creates a random neopixel flicker. Any unsupplied argument is
        set at random, except for `final_color` that defaults to
        (0, 0, 0).
        """
        i = i or random.randint(0, self.n_total - 1)
        steps = steps or random.randint(self.min_steps, self.max_steps)
        initial_color = initial_color or self.random_color(
            self.red_range, self.green_range, self.blue_range
        )
        final_color = final_color or self.random_color(
            self.red_range, self.green_range, self.blue_range
        )

        self.total_steps[i] = steps
        self.current_step[i] = 0
        self.initial_color[i] = initial_color
        self.color_deltas[i] = (
            (final_color[0] - initial_color[0]) / (steps - 1),
            (final_color[1] - initial_color[1]) / (steps - 1),
            (final_color[2] - initial_color[2]) / (steps - 1),
        )

    def update(self):
        """
        Please 🙏 call me at each tick to update the LEDs
        """
        for i in range(self.n_total):
            c = self.current_step[i]
            if c < self.total_steps[i]:
                self.current_step[i] += 1
                I = self.initial_color[i]
                d = self.color_deltas[i]
                self[i] = (
                    round(I[0] + c * d[0]),
                    round(I[1] + c * d[1]),
                    round(I[2] + c * d[2]),
                )

    @staticmethod
    def random_color(red_range, green_range, blue_range):
        return (
            random.randint(*red_range),
            random.randint(*green_range),
            random.randint(*blue_range),
        )
