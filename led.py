import RPi.GPIO as GPIO

FREQ = 50

class RGBLed:
    """
    Class to handle controlling an RGB LED
    """

    #LED COLOR CONSTANTS
    RED             = (255,0,0)
    GREEN           = (0,255,0)
    BLUE            = (0,0,255)
    YELLOW          = (255,255,0)
    ORANGE          = (255,135,0)
    PURPLE          = (255,0,255)
    CYAN            = (0,255,0)
    LED_OFF         = (0,0,0)    

    def __init__(self, r, g, b):
        """
        This classes uses RPi.GPIO objects

        Args:
            r (int): GPIO pin number for red LED
            g (int): GPIO pin number for green LED
            b (int): GPIO pin number for blue LED
        """
        self._red_io = r
        self._green_io = g
        self._blue_io = b

        GPIO.setup(self._red_io, GPIO.OUT)
        GPIO.setup(self._green_io, GPIO.OUT)
        GPIO.setup(self._blue_io, GPIO.OUT)

        self.r = GPIO.PWM(self._red_io, FREQ)  
        self.g = GPIO.PWM(self._green_io, FREQ)
        self.b = GPIO.PWM(self._blue_io, FREQ)
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
