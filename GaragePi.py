
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


class RGBLed():
    """
    Class to handle controlling an RGB LED
    """
    def __init__(self,r,g,b):
        """
        Args:
            r (GPIO.PWM): GPIO.PWM object tied to red LED
            g (GPIO.PWM): GPIO.PWM object tied to green LED
            b (GPIO.PWM): GPIO.PWM object tied to blue LED
        """        
        self.r = r
        self.g = g
        self.b = b
        
        #init LED to be off
        self.r.start(0)
        self.g.start(0)
        self.b.start(0)

    def set_color(self,color_code):
        """
        Set the color of the LED
        
        Args:
            color_code (tuple): desired color in the form (red,green,blue) and in the range 0-255 per component
        """
        #scale the RGB codes to be 0-100
        R = (color_code[0] / 255) * 100
        G = (color_code[1] / 255) * 100
        B = (color_code[2] / 255) * 100
        #update the duty cycles for each leg of the LED
        self.r.ChangeDutyCycle(R)
        self.g.ChangeDutyCycle(G)
        self.b.ChangeDutyCycle(B)
        
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
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
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
    reads a text file with the stored MQTT credentials are returns the username and password
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
        try:
            f.close()
        except:
            pass 

  
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
    
    
def toggle_garage_opener(door):
    """
    Function to toggle either door 1 or door 2 button
    
    Args:
        door (int) Door 1 (1) Door 2 (2)
    """
    if door == DOOR1:
        pin = DOOR1_CTRL
    elif door == DOOR2:
        pin = DOOR2_CTRL
    else:
        raise Exception("Invalid door argument (%d)"%door)
        
    GPIO.output(pin,GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(pin,GPIO.LOW)
    
def get_door_state(door):
    """
    Function to get the state of the door
    
    Args:
        door (int) Door 1 (1) Door 2 (2)
        
    Returns:
        state (int): 0 (open) 1 (closed)
    """
    if door == DOOR1:
        pin = DOOR1_CTRL
    elif door == DOOR2:
        pin = DOOR2_CTRL
    else:
        raise Exception("Invalid door argument (%d)"%door)
        
    return GPIO.input(pin)
    
    
    
def read_dht22(client,poll_time=60):
    """
    Read the temperature and humidty and publish results to the appropriate topics
    
    Args:
        client (obj): MQTT client object
        poll_time (int): Number of seconds between readings
    """
    sensor = Adafruit_DHT.DHT22
    while True:
        try:
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin, DHT22_DATA)
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
    else:
        #unrecognized command
        logger.debug("Unrecognized command (%s) on topic: %s"%(message.payload,message.topic))
 
    
    
#### Main ####
init_logger(LOG_FILE_PATH)      #initialize the logging object
logger = logging.getLogger('Main')

username,password = import_credentials()
mqttClient = MQTTComms(BROKER_HOST,'GaragePi',SUBSCRIPTION_TOPICS,username,password)

