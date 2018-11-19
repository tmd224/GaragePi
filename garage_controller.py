import time
import logging
import RPi.GPIO as GPIO
from MQTTComms import message_callback


class GarageDoor:
    """
    Class that models a physical garage door bay
    """

    def __init__(self, door, ctrl_pin, state_pin, client, ctrl_topic, state_topic):
        """
        Constructor for GarageDoor

        Args:
            door (int): Door number
            ctrl_pin (int): GPIO pin number that controls door
            state_pin (int): GPIO pin number that monitors the state of the door
            client (MQTTComms): MQTT comms object
        """
        self.door = door
        self.ctrl_pin = ctrl_pin
        self.state_pin = state_pin
        self._client = client
        self.ctrl_topic = ctrl_topic
        self.state_topic = state_topic
        self.logger = logging.getLogger("DOOR%s" % door)

        self.logger.debug("Initializing Garage Door")

        # initialize GPIO pin
        GPIO.setup(self.ctrl_pin, GPIO.OUT)
        GPIO.setup(self.state_pin, GPIO.IN)
        GPIO.add_event_detect(self.state_pin, GPIO.BOTH, callback=self.update_state)

        self.state = self._update_state()

        self._client.subscribe(self.ctrl_topic)
        self._client.subscribe(self.state_topic)
        self.client.add_message_callback(self.ctrl_topic, self.process_cmd)

    def push_button(self):
        """
        Method to toggle the garage door button.  This will open or close the door depending on the
        current state of the door.
        """
        self.logger.debug("push_button() called")
        GPIO.output(self.ctrl_pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(self.ctrl_pin, GPIO.LOW)

    def update_state(self):
        """
        Update state of garage door
        """
        self.state = GPIO.input(self.state_pin)
        state_str = 'CLOSED' if self.state else 'OPEN'
        self.logger.debug('Door State: %s' % state_str)
        self._client.publish(self.state_topic, self.state)

    @message_callback
    def process_cmd(self, client, userdata, message):
        """
        Process commands
        """
        if message == CMD_OPEN:
            self.push_button()
        elif message == CMD_CLOSE:
            self.push_button()
        else:
            self.logger.debug('Invalid command: %s' % message)
