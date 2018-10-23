
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
CMD_1 = 'hass/cover1/set'           #Door1 Cmd topic
CMD_2 = 'hass/cover2/set'           #Door2 Cmd topic
STATE_1 = 'hass/cover1/state'       #Door1 State topic  
STATE_2 = 'hass/cover2/state'       #Door2 state topic
TEMP = 'hass/heat/val'              #Temperature sensor topic
HUMDITY = 'hass/humidty/val'        #Humidity sensor topic  
PIR = 'hass/pir/state'              #PIR sensor topic

SUBSCRIPTION_TOPICS = [CMD_1,CMD_2,STATE_1,STATE_2,TEMP,HUMDITY,PIR]

#GPIO CONSTANTS
DHT22_DATA = 27                 #data pin for DHT22 Temp/Humidity sensor

def message_callback(callback):
    """
    Decorator function for mqtt message callbacks
    """
    @wraps(callback)    #update attribute data for decorator
    def message_handler(client,userdata,message):
        #decode and log the message and return the payload values
        msg = message.payload.decode("utf-8")
        logger.debug('Received Message: %s (%s)'%(msg,message.topic))
        return callback(client,userdata,msg)
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
    GPIO.setup(LED,GPIO.OUT)
    GPIO.setup(DOOR_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
def read_dht22(client,poll_time=60):
    """
    Read the temperature and humidty and publish results to the appropriate topics
    
    Args:
        client (obj): MQTT client object
        poll_time (int): Number of seconds between readings
    """
    sensor = Adafruit_DHT.DHT22
    while 1:
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
    
@message_callback
def cover_cmd_callback(client,userdata,message):
    print('Message: %s | Type: %s'%(message,type(message)))
    
    
    
    
#### Main ####
init_logger(LOG_FILE_PATH)      #initialize the logging object
logger = logging.getLogger('Main')

username,password = import_credentials()
client = MQTTComms(BROKER_HOST,'GaragePi',SUBSCRIPTION_TOPICS,username,password)

