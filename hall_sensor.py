from machine import ADC, Pin
from utime import sleep
from math import sqrt
import network
import socket
import time
import ubinascii
from umqtt.simple import MQTTClient
import secrets


# Default MQTT server to connect to
mqtt_server = secrets.mqtt_server 
mqtt_user = secrets.mqtt_user
mqtt_pass = secrets.mqtt_password
client_id = secrets.client_id
print(client_id)
TOPIC = "george-o-meter/{0}".format(client_id)

ssid = secrets.ssid  #Wireless SSIS
password = secrets.ssid_pass #Wireless SSID Password

#Turn on the onboard LED 
led = machine.Pin("LED", machine.Pin.OUT)
led.on()


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
  if wlan.status() < 0 or wlan.status() >= 3:
    break
  max_wait -= 1
  print('waiting for connection...')
  led.off()
  time.sleep(1)
  led.on()
 
# Handle connection error
if wlan.status() != 3:
   raise RuntimeError('network connection failed')
else:
  print('connected')
  status = wlan.ifconfig()
  print( 'ip = ' + status[0] )

hall_sensor = ADC(26)

def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, keepalive=3600, user=mqtt_user, password=mqtt_pass)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

global last_reading
last_reading = 3.3  ## Record last to make sure wheel is going around and not just staying there.

conversion_factor = 3.3 / (65535)

global counter
counter = 0


def batch_read():
    global counter
    global last_reading
    i = 0
    #This tries to approximate a 10 second period.  Its probably not real accurate.
    while i < 100:
        current_reading = read_sensor()
        current_diff = last_reading - current_reading
        if current_diff > 2:
            counter = counter + 1
        last_reading = current_reading
        i = i + 1
        sleep(0.1)
    return(counter)

def read_sensor():
    reading = hall_sensor.read_u16() * conversion_factor
    return (reading)
try:
    client = mqtt_connect()
except OSError as e:
    reconnect()
while True:
    try:
        counts = batch_read()
    except:
        print("Error occurred during batch read")
    try:    
        data_string = b'{{"rotations":{0}}}'.format(counter)
        print(data_string)
        client.publish(TOPIC, data_string)
        #reset counter on successful publish
        counter = 0
    except:
        reconnect()
    sleep(0.1)    
        

