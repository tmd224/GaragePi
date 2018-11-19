import RPi.GPIO as GPIO


class RGBLed:
    """
    Class to handle controlling an RGB LED
    """

    def __init__(self, r, g, b):
        """
        This classes uses RPi.GPIO objects

        Args:
            r (int): GPIO pin number for red LED
            g (int): GPIO pin number for green LED
            b (int): GPIO pin number for blue LED
        """
        self.r = r
        self.g = g
        self.b = b

        GPIO.setup(r, GPIO.OUT)
        GPIO.setup(g, GPIO.OUT)
        GPIO.setup(b, GPIO.OUT)

        # init LED to be off
        self.r.start(0)
        self.g.start(0)
        self.b.start(0)

    def set_color(self, color_code):
        """
        Set the color of the LED

        Args:
            color_code (tuple): desired color in the form (red,green,blue) and in the range 0-255 per component
        """
        # scale the RGB codes to be 0-100
        r = (color_code[0] / 255) * 100
        g = (color_code[1] / 255) * 100
        b = (color_code[2] / 255) * 100
        # update the duty cycles for each leg of the LED
        self.r.ChangeDutyCycle(r)
        self.g.ChangeDutyCycle(g)
        self.b.ChangeDutyCycle(b)
