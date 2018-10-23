
import time
import logging
import threading
import paho.mqtt.client as mqtt

CONNECT_RESPONSE = {0: 'Connection successful',
                    1: 'Connection refused - incorrect protocol version',
                    2: 'Connection refused - invalid client identifier',
                    3: 'Connection refused - server unavailable',
                    4: 'Connection refused - bad username or password',
                    5: 'Connection refused - not authorised',
                   }

                   
class MQTTComms():
    """
    General class to encapsulate MQTT communication
    This class uses re-entrant locks to ensure thread safety on publish events
    
    #Documentation https://pypi.org/project/paho-mqtt/#usage-and-api
    
    """
    
    def __init__(self,broker,name="MQTT Client",topics=None,username=None,password=None,**kwargs):
        """
        Constructor
        
        Args:
            topics (list): list of topics to subscribe to in string format
            username (str): username
            password (str): password
            
        Keyword Args:
            message_callback: handle to function to handle message callbacks
        
        """
        self.logger = logging.getLogger(self.__class__.__name__) #add a new logger handle
        self.lock = threading.RLock()
        self.broker = broker
        self.name = name
        self.topics = topics
        self._username = username
        self._password = password
        
        self._message_callback = kwargs.pop('message_callback')
        #Argument checking
        if broker is None or type(broker) != type(str()):
            ErrorString = "broker is None type, a valid broker in string format must be provided"
            self.logger.error(ErrorString)
            raise Exception(ErrorString)
            
        self.client = mqtt.Client(name)     #create MQTT client object
        self.client.username_pw_set(self._username,self._password)      #configure client credentials
        
        #register call_backs
        self.client.on_log = self._on_log_callback
        self.client.on_message = self._on_message_callback
        self.client.on_connect = self._on_connect_callback
        

    
    def connect(self):
        """
        Connect the MQTT client
        """
        self.client.connect(self.broker)
        self.client.loop_start()
        
        #subscribe to topics
        for topic in self.topics:
            self.client.subscribe(topic)        
        
    def close(self):
        """
        Close MQTT client connection
        """
        self.client.loop_stop()
        self.client.disconnect()
        
    def add_message_callback(self,topic,callback):
        """
        Register a callback function for a given callback
        
        Args:
            topic (str): topic to bind callback to
            callback (obj): handle to callback function
        """
        self.client.message_callback_add(topic, callback)
        
    def publish(self,topic, msg):
        """
        Publish a message on a given topic
        
        Args:
            topic (str): topic to publish to
            msg (int,str): msg to publish
        """
        self._get_mutex()
        self.client.publish(topic,msg)
        
    def _get_mutex(self):
        """
        Blocking method to wait for the thread lock to clear.  Keeps track of
        how many attempts are made
        """
        attempts = 0
        wait_time = 0.5     #seconds
        lock_status = self.lock.acquire(0)  #attempt to get the lock
        if lock_status:
            return  #return if we got the lock
        else:
            #wait until we get the lock
            while lock_status == False:
                time.sleep(0.5)
                attempts += 1
                lock_status = self.lock.acquire(0)
            
            self.logger.debug('mutex acquired after %d attempts (%.2f sec)'%(attempts,attempts*wait_time))
            
    def _on_log_callback(self, client, userdata, level, buf):
        """
        logging callback
        """
        self.logger.debug(buf)
        
    def _on_connect_callback(self, client, userdata, flags, rc):
        """
        This callback gets called during a client connection
        """
        if rc > 5:
            self.logger.info("Unsuccessful client connection - Error code unknown (%d)"%rc)
            self.client.bad_connection_flag=True
        else:
            self.logger.info("MQTT Client Connection Response: %s (%d)"%(CONNECT_RESPONSE[rc],rc))
            self.client.connected_flag=True #Flag to indicate success        
           
    def _on_message_callback(self, client,userdata,message):
        """
        This callback gets called when messages are received
        """
        msg = message.payload.decode("utf-8")
        self.logger.info('Received Message: %s'%msg)
        self._message_callback(msg)
        
        