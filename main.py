import logging
import threading
import RPi.GPIO as GPIO
from MQTTComms import MQTTComms
from dht22_sensor import dht_sensor
from utils import init_logger, import_credentials

LOG_FILE_PATH = "garagePi.log"
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
DOOR1_CTRL      = 17            # output pin controlling door 1
DOOR2_CTRL      = 22            # output pin controlling door 2
DOOR1_STATE     = 5             # input pin for determining state of door 1
DOOR2_STATE     = 6             # input pin for determining state of door 2
PIR_STATE       = 26            # input pin for determining state of PIR sensor
DHT22_DATA      = 27            # data pin for DHT22 Temp/Humidity sensor
LED_RED         = 23            # output pin for Red RGB LED pin
LED_GREEN       = 24            # output pin for Green RGB LED pin
LED_BLUE        = 25            # output pin for Blue RGB LED pin

init_logger(LOG_FILE_PATH)  # initialize logger
_LOGGER = logging.getLogger("Main")
_LOGGER.info("Initializing GaragePi")

username, password = import_credentials(MQTT_CREDENTIALS)   # get broker credentials
mqttClient = MQTTComms(BROKER_HOST, 'GaragePi', [], username, password)  # setup MQTT Client object

GPIO.setmode(GPIO.BCM)

main_thread = threading.currentThread()

dht = dht_sensor(DHT22_DATA, mqttClient, TEMP, HUMIDITY)
dht_thread = threading.Thread(name="DHT_Sensor", target=dht.start_polling)

dht_thread.start()  #start the DHT thread

