# Shine Bright Like a Diamond

A firefly inspired tiara that shines bright when dancing.

## Hardware

1. [Adafruit Gemma M0.](https://www.adafruit.com/product/3501)
2. [Medium Vibration Sensor Switch.](https://www.adafruit.com/product/3501)
3. [Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels](https://www.adafruit.com/product/4560)
4. Pull down resistor.

The NeoPixels are connected to Gemma's `A1` port, `GND` and `Vout`.
And the vibration sensor is connected between `3v3` port and `A2`, with
a pull down resistor to `A2`.

## Code

This project uses [CircuitPython](https://circuitpython.org/).

The main script imports the `NeoPixelFirefly` class from
[npfirefly](shine_bright_like_a_diamond/npfirefly.py) library. _Feel
free to download and `flicker` your own fireflies._. Configurations
for the NeoPixels are:

```python
    # NeoPixels configuration
    PIXEL_PIN = board.A1  # Adafruit Gemma M0
    NUM_PIXELS = 50  # Adafruit Soft Flexible Wire NeoPixel Strand - 50 NeoPixels
    BRIGHTNESS = 1.0
    MIN_STEPS = 8  # Minimum firefly flicker timesteps
    MAX_STEPS = 127  # Maximum firefly flicker timesteps
    RED_RANGE = (127, 255)  # Red random color range
    GREEN_RANGE = (15, 63)  # Green random color range
    BLUE_RANGE = (0, 7)  # Blue random color range
```

Then, a vibration sensor detects movement and starts new fireflies. The
sensor is not designed to be accurate detecting movement. In fact it's
just a switch that triggers with movement. To counter that a moving
average algorithm detects sudden changes in the sensors values to
increase the number of fireflies. Because of that the tiara is very
sensitive to random noises in the sensor, what is kind of cool actually.
You may need to tweak the configurations for your your sensor for best
results:

```python
    # Vibration sensor configuration
    SENSOR_WINDOW = 64  # Moving average window
    SENSOR_MEAN_MIN_DEV_PERC = 0.09  # Mean minimum deviation in percent value
    SENSOR_BASELINE_OUTLIERS = 0.2  # Baseline measure
    SENSOR_SENSIBILITY = 0.2  # Sensor sensibility
```

## License

> This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
>
> This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
>
> You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
