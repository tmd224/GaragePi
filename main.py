import time
import logging
import threading
import RPi.GPIO as GPIO
from MQTTComms import MQTTComms
from dht22_sensor import dht_sensor
from garage_controller import GarageDoor
from utils import init_logger, import_credentials
from threads import DroneThread
from led import RGBLed

# LOGGER
LOG_FILE_PATH = "garagePi.log"
CONSOLE_LEVEL = logging.DEBUG
LOG_LEVEL = logging.DEBUG

# MQTT
MQTT_CREDENTIALS = 'credentials.txt'

BROKER_HOST = '192.168.1.120'

# MQTT Topics
CMD_1 = 'hass/cover1/set'                       # Door1 Cmd topic
CMD_2 = 'hass/cover2/set'                       # Door2 Cmd topic
STATE_1 = 'hass/cover1/state'                   # Door1 State topic
STATE_2 = 'hass/cover2/state'                   # Door2 state topic
AVAILABILITY_1 = 'hass/cover1/availability'     # Door1 availability topic
AVAILABILITY_2 = 'hass/cover2/availability'     # Door2 availability topic
TEMP = 'hass/heat/val'                          # Temperature sensor topic
HUMIDITY = 'hass/humidty/val'                   # Humidity sensor topic
PIR = 'hass/pir/state'                          # PIR sensor topic

# GPIO CONSTANTS
DOOR1_CTRL      = 24            # output pin controlling door 1
DOOR2_CTRL      = 8             # output pin controlling door 2
DOOR1_STATE     = 23            # input pin for determining state of door 1
DOOR2_STATE     = 25            # input pin for determining state of door 2
PIR_STATE       = 26            # input pin for determining state of PIR sensor
DHT22_DATA      = 27            # data pin for DHT22 Temp/Humidity sensor
LED_RED         = 0             # output pin for Red RGB LED pin
LED_GREEN       = 5             # output pin for Green RGB LED pin
LED_BLUE        = 6             # output pin for Blue RGB LED pin

init_logger(LOG_FILE_PATH, CONSOLE_LEVEL, LOG_LEVEL)  # initialize logger
_LOGGER = logging.getLogger("Main")
_LOGGER.info("Initializing GaragePi")

username, password = import_credentials(MQTT_CREDENTIALS)   # get broker credentials
mqttClient = MQTTComms(BROKER_HOST, 'GaragePi', [], username, password)  # setup MQTT Client object
mqttClient.connect()
time.sleep(3)

GPIO.setmode(GPIO.BCM)

main_thread = threading.currentThread()

dht = dht_sensor(DHT22_DATA, mqttClient, TEMP, HUMIDITY)
dht_thread = DroneThread(name="DHT_Sensor", target=dht.read_sensor, kwargs={'LoopDelay':5})

led = RGBLed(LED_RED, LED_GREEN, LED_BLUE)
led.set_color(RGBLed.BLUE)

door1 = GarageDoor(1, DOOR1_CTRL, DOOR1_STATE, mqttClient, CMD_1, STATE_1, led)

try:
    dht_thread.start()  #start the DHT thread
    while True:
        _LOGGER.debug("Main Loop Heart Beat")
        time.sleep(10)
except KeyboardInterrupt:
    dht_thread.join()
    _LOGGER.debug("Waiting for threads to join")    
finally:
    _LOGGER.debug("Disconnecting MQTT Client")
    mqttClient.close()
    _LOGGER.debug("Cleaning up GPIO")
    GPIO.cleanup()
    _LOGGER.debug("Ending Main")