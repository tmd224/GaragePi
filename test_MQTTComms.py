
import time
import random
import logging
import RPi.GPIO as GPIO
from MQTTComms import MQTTComms

#Documentation https://pypi.org/project/paho-mqtt/#usage-and-api

#CONSTANTS
LED = 17
DOOR_INPUT = 26

#MQTT CONSTANTS

LOG_FILE_PATH = "test.log"

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

    
    


CONNECT_RESPONSE = {0: 'Connection successful',
                    1: 'Connection refused - incorrect protocol version',
                    2: 'Connection refused - invalid client identifier',
                    3: 'Connection refused - server unavailable',
                    4: 'Connection refused - bad username or password',
                    5: 'Connection refused - not authorised',
                   }



state_topic = ['hass/mqtt_test/cmd','hass/mqtt_test/val']


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
        f = open('credentials.txt', 'r')
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
        main_log.error("Error importing credentials file: %s"%e)
    finally:
        try:
            f.close()
        except:
            pass

def setup_gpio():
    """
    Initial setup of the GPIO
    """ 
    main_log.info("Setting up GPIO")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED,GPIO.OUT)
    GPIO.setup(DOOR_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
def parse_commands(command):
    """
    Function to parse all incoming commands
    """
    if command == "LED_ON":
        main_log.info("Turning LED ON")
        GPIO.output(LED,GPIO.HIGH)
        time.sleep(3)
        client.publish(state_topic[1], 1)
    elif command == "LED_OFF":
        main_log.info("Turning LED OFF")
        GPIO.output(LED,GPIO.LOW)
        time.sleep(3)
        client.publish(state_topic[1], 0)        
        
     
        
init_logger(LOG_FILE_PATH)    
#add logger devices
main_log = logging.getLogger('MAIN')
    
setup_gpio()
#client = mqtt_init()
broker = '192.168.1.120'
username,password = import_credentials()
client = MQTTComms(broker,'HASS MQTT',state_topic,username,password,**{'message_callback':parse_commands})

delay = 5
val = 0
try:
    main_log.info("Entering Main Loop")
    while True:
        pass
        # if val > 20:
            # val = 0
            
        # client.publish(state_topic, val)
        # main_log.info("Publishing value: %d"%val)
        # val += 1
        # time.sleep(delay)

except KeyboardInterrupt:
    main_log.info("Stopping MQTT Client")
    #client.loop_stop()
    #client.disconnect()
    client.close()
    GPIO.cleanup()
    

    
    
    
