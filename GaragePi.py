
import time
import logging
import threading
import RPi.GPIO as GPIO
from functools import wraps
from MQTTComms import MQTTComms
import Adafruit_DHT


LOG_FILE_PATH = "garagePi.log"
MQTT_CREDENTIALS = 'credentials.txt'

BROKER_HOST = '192.168.1.120'

#MQTT Topics
CMD_1 = 'hass/cover1/set'                       #Door1 Cmd topic
CMD_2 = 'hass/cover2/set'                       #Door2 Cmd topic
STATE_1 = 'hass/cover1/state'                   #Door1 State topic  
STATE_2 = 'hass/cover2/state'                   #Door2 state topic
AVAILABILITY_1 = 'hass/cover1/availability'     #Door1 availability topic
AVAILABILITY_2 = 'hass/cover2/availability'     #Door2 availability topic
TEMP = 'hass/heat/val'                          #Temperature sensor topic
HUMDITY = 'hass/humidty/val'                    #Humidity sensor topic  
PIR = 'hass/pir/state'                          #PIR sensor topic

SUBSCRIPTION_TOPICS = [CMD_1,CMD_2,STATE_1,STATE_2,AVAILABILITY_1,AVAILABILITY_2,TEMP,HUMDITY,PIR]

#MQTT COMMANDS
CMD_OPEN        = 'OPEN'
CMD_CLOSE       = 'CLOSE'
CMD_STOP        = 'STOP'
STATE_OPEN      = 'open'
STATE_CLOSED    = 'closed'
STATE_ONLINE    = 'online'
STATE_OFFLINE   = 'offline'

#GPIO CONSTANTS
DOOR1_CTRL      = 17            #output pin controlling door 1
DOOR2_CTRL      = 22            #output pin controlling door 2
DOOR1_STATE     = 5             #input pin for determining state of door 1
DOOR2_STATE     = 6             #input pin for determining state of door 2
PIR_STATE       = 26            #input pin for determining state of PIR sensor
DHT22_DATA      = 27            #data pin for DHT22 Temp/Humidity sensor
LED_RED         = 23            #output pin for Red RGB LED pin
LED_GREEN       = 24            #output pin for Green RGB LED pin
LED_BLUE        = 25            #output pin for Blue RGB LED pin

#LED COLOR CONSTANTS
RED             = (255,0,0)
GREEN           = (0,255,0)
BLUE            = (0,0,255)
YELLOW          = (255,255,0)
ORANGE          = (255,135,0)
PURPLE          = (255,0,255)
CYAN            = (0,255,0)
LED_OFF         = (0,0,0)

#Other constants
DOOR1           = 1
DOOR2           = 2
DOOR_OPEN       = 0
DOOR_CLOSED     = 1



def message_callback(callback):
    """
    Decorator function for mqtt message callbacks
    """
    @wraps(callback)    #update attribute data for decorator
    def message_handler(client,userdata,message):
        #decode and log the message and return the payload values
        message.payload = message.payload.decode("utf-8")
        logger.debug('Received Message: %s (%s)'%(message.payload,message.topic))
        return callback(client,userdata,message)
    return message_handler
    

def init_logger(fullpath):
    """
    Setup the logger object
    
    Args: 
        fullpath (str): full path to the log file 
    """
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(threadName)-10s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d-%y %H:%M:%S',
                        filename=fullpath,
                        filemode='w')
                        
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logging.debug("Creating log file")
    
    
def import_credentials():
    """
    reads a text file with the stored MQTT credentials and returns the username and password
    Text file format is:
    USERNAME=ThisIsAUserName
    PASSWORD=ThisIsAPassword
    
    All leading and trailing spaces will be stripped from the username/password
    """
    username = None
    password = None
    try:
        f = open(MQTT_CREDENTIALS, 'r')
        lines = f.readlines()
        for line in lines:
            #look for username, password and parse out the values.
            tmpLine = line.upper()
            if "USERNAME" in tmpLine:
                #this line contains the username, so parse it out.
                username = line.split('=')[1].strip()   #split the line by '=', take the second part and strip whitespace
            elif "PASSWORD" in tmpLine:
                password = line.split('=')[1].strip() 
                
        return username,password
        
    except Exception as e: 
        logger.error("Error importing credentials file: %s"%e)
    finally:
        if f:
            f.close()

  
def setup_gpio():
    """
    Initial setup of the GPIO
    """ 
    logger.info("Setting up GPIO")
    GPIO.setmode(GPIO.BCM)
    
    #outputs
    GPIO.setup(DOOR1_CTRL, GPIO.OUT)
    GPIO.setup(DOOR2_CTRL, GPIO.OUT)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_BLUE, GPIO.OUT)
    
    #inputs
    GPIO.setup(DOOR1_STATE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(DOOR2_STATE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIR_STATE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(DHT22_DATA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
def read_dht22(client,poll_time=60):
    """
    Read the temperature and humidity and publish results to the appropriate topics
    
    Args:
        client (obj): MQTT client object
        poll_time (int): Number of seconds between readings
    """
    sensor = Adafruit_DHT.DHT22
    while True:
        try:
            humidity, temperature = Adafruit_DHT.read_retry(sensor, DHT22_DATA, 1)
            if temperature is not None and humidity is not None:
                temperature = temperature * (9/5.0) + 32
                #publish to mqtt
                client.publish(TEMP,"%.1f"%temperature)
                client.publish(HUMDITY,"%.1f"%humidity)

        except Exception as e:
            logger.error("Caught exception: %s"%e)

        time.sleep(poll_time)
        
def cleanup():
    """
    Cleanup GPIO
    """
    GPIO.cleanup()
    client.close()
    
#MQTT Message Callback functions

@message_callback
def cover_cmd_callback(client,userdata,message):
    """
    Message callback for garage cmd topic
    """
    if message.topic == CMD_1:
        door = DOOR1
    elif message.topic == CMD_2:
        door = DOOR2
    else:
        logger.debug("Invalid topic (%s) for cover_cmd_callback() - Payload: %s"%(message.topic,message.payload))
        return
        
    if message.payload == CMD_OPEN:
        #open garage door
        toggle_garage_opener(door)

    elif message.payload == CMD_CLOSE:
        #close garage door
        toggle_garage_opener(door)
        
    elif message.payload == CMD_STOP:
        #stop garage door
        pass
    else:
        #unrecognized command
        logger.debug("Unrecognized command (%s) on topic: %s"%(message.payload,message.topic))

        
class GarageDoor:
    """
    Class that models a physical garage door bay
    """
    def __init__(self, door, ctrl_pin, state_pin, client):
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
        self.logger = logging.getLogger("DOOR%s"%door)
        
        self.logger.debug("Initializing Garage Door")
        
        self.state = self.get_state()
        
    def get_state(self):
        """
        This method reads the door state sensor and returns the current state
        
        Returns:
            state (bool): True - Close, False - Open
        """
        self.state = GPIO.input(self.state_pin)
        state_str = 'CLOSED' if self.state else 'OPEN'
        self.logger.debug('Door State: %s'%state_str)
        return self.state
        
    def push_button(self):
        """
        Method to toggle the garage door button.  This will open or close the door depending on the 
        current state of the door.
        """
        self.logger.debug("push_button() called")
        GPIO.output(self.ctrl_pin,GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(self.ctrl_pin,GPIO.LOW)
    
    @message_callback
    def process_cmd(self,client,userdata,message):    
        """
        Process commands
        """
        if message == CMD_OPEN:
            self.push_button()
        elif message == CMD_CLOSE:
            self.push_button()
        else:
            self.logger.debug('Invalid command: %s'%message)

    
#### Main ####
init_logger(LOG_FILE_PATH)      #initialize the logging object
logger = logging.getLogger('Main')

username,password = import_credentials()
mqttClient = MQTTComms(BROKER_HOST,'GaragePi',SUBSCRIPTION_TOPICS,username,password)

