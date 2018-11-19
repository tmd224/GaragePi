import time
import logging
import Adafruit_DHT
import RPi.GPIO as GPIO

class dht_sensor:
    """
    Class to model dht22 temperature and humidity sensor
    """
    def __init__(self, data_pin, client, temp_topic, hum_topic):
        """
        Args:
            data_pin (int): RPI pin number connected to dht22 data pin
            client (MQTTComms): Handle to MQTTComms client object
            temp_topic (str): Temperature state MQTT topic
            hum_topic (str): Humidity state MQTT topic

        """
        self.pin = data_pin
        self._client = client

        self._temp_topic = temp_topic
        self._hum_topic = hum_topic
        self._temp = None
        self._humidity = None

        self._last_temp = None
        self._last_humidity = None

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # set data pin to be an input
        self._sensor = Adafruit_DHT.DHT22
        self.logger = logging.getLogger(__class__.__name__)

        self._client.subscribe(self._temp_topic)
        self._client.subscribe(self._hum_topic)

    def update_temp(self, temp):
        """
        Update the temp topic with the latest temp value.

        Args:
            temp (float): Latest temperature value from sensor
        """
        self._temp = temp
        if self._temp != self._last_temp:
            self._last_temp = self._temp    # update last temp with the latest
            self._client.publish(self._temp_topic, self._temp)

    def update_humidity(self, humidity):
        """
        Update the Humidity topic with the latest humidity value

        Args:
            humidity (float): Latest humidity value from the sensor
        """
        self._humidity = humidity
        if self._humidity != self._last_humidity:
            self._last_humidity = self._humidity
            self._client.publish(self._hum_topic, self._humidity)

    def start_polling(self, poll_time=60):
        """
        Get a new reading from the sensor.  This function is meant to be run on a thread.

        Args:
            poll_time (int): Number of seconds between readings
        """

        while True:
            try:
                humidity, temperature = Adafruit_DHT.read_retry(self._sensor, self.pin, 1)
                if temperature is not None and humidity is not None:
                    temperature = temperature * (9 / 5.0) + 32
                    self.logger.debug("Temp: %.1f F | Humidity: %.1f %", temperature, humidity)
                    self.update_temp(temperature)
                    self.update_humidity(humidity)

            except Exception as e:
                self.logger.error("Caught exception: %s" % e)

            time.sleep(poll_time)
