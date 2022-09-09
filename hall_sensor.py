from machine import ADC, Pin
from utime import sleep
from math import sqrt

import network
import socket
import time
import urequests

#Endpoint of your influxdb, currently plaintext and unauthenticated
influx_url = "http://192.168.10.24:8086/write?db=george"  
ssid = 'SSID'  #Wireless SSID
password = 'SSIDPASSWORD' #Wireless SSID Password

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


global last_reading
last_reading = 3.3  ## Record last to make sure wheel is going around and not just staying there.

conversion_factor = 3.3 / (65535)

global counter
counter = 0


def batch_read():
    global counter
    global last_reading
    i = 0
    while i < 20:
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

while True:
    try:
        counts = batch_read()
    except:
        print("Error occurred during batch read")
    try:    
        data_string = "Counter count={0}".format(counter)
        print(data_string)
        response = urequests.post(influx_url, data=data_string)
        print(response.text)
        counter = 0
    except:
        print("influxdb error")
    sleep(0.2)
