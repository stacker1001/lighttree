# coding=utf-8
 
import RPi.GPIO as GPIO
import datetime
import pyttsx3
import logging
import os

logger = logging.getLogger(__name__)

#engine = pyttsx3.init(driverName='dummy', debug=True)
engine = pyttsx3.init()

engine.say("Race")
engine.runAndWait()

#os.system(f"espeak 'Hello'")

def my_callback_pressed(channel):
    if GPIO.input(channel) == GPIO.LOW:
        print('\n▼  at ' + str(datetime.datetime.now()))
    #else:
    #    print('\n ▲ at ' + str(datetime.datetime.now())) 
        #engine.say("Stop")
        #engine.runAndWait()

def my_callback_released(channel):
    if GPIO.input(channel) == GPIO.HIGH:
        print('\n ▲ at ' + str(datetime.datetime.now())) 
    #else:
    #    print('\n ▲ at ' + str(datetime.datetime.now())) 

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(23, GPIO.FALLING, bouncetime=1000, callback=my_callback_pressed)
    GPIO.add_event_detect(23, GPIO.RISING, bouncetime=1000, callback=my_callback_released)

    message = input('\nPress any key to exit.\n')
 
finally:
    GPIO.cleanup()
 
print("Goodbye!")