import RPi.GPIO as GPIO


class PIR:
    """
    Class to model PIR motion sensor
    """
    def __init__(self, pin, client):
        """
        Args:
            pin (int): RPI input pin for PIR sensor
            client (MQTTComms): MQTT client
        """
        self._pin = pin
        self._client = client
        self.logger = logging.getLogger(__class__.__name__)

        self.state = 0

        # initialize GPIO pin
        GPIO.setup(self._pin, GPIO.IN)
        GPIO.add_event_detect(self._pin, GPIO.BOTH, callback=self._update_state)

    def get_state(self):
        """
        Get the state of the PIR sensor

        Returns:
            state (int)
        """
        return self.state

    def _update_state(self):
        """
        Update the state of when interrupt fires
        """
        self.state = GPIO.input(self._pin)
