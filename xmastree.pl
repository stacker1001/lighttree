#!/usr/bin/python
import RPi.GPIO as GPIO
import sys
import time

GPIO.setmode(GPIO.BCM)

# Relays 1 through 8, in order.  These are active-LOW pins, i.e., sending a LOW
# output turns on the corresponding relay, and sending a HIGH turns off the
# relay.
pins = [18, 25, 10, 24, 23, 22, 27, 17]

# These are the two hardware pushbutton inputs; the input will show 0 if the
# button is pressed, 1 if it's not.
#
# "READY" button on post
btnREADY = 9
# Actual start button
btnSTART = 7    

#RuntimeWarning: This channel is already in use, continuing anyway.
#Use GPIO.setwarnings(False) to disable warnings.
GPIO.setwarnings(False)

def showInitializationSequence():
  for p in range(0, 5):
    for rep in range(1,4):
      GPIO.output(pins[p], GPIO.LOW)
      time.sleep(0.0625)
      GPIO.output(pins[p], GPIO.HIGH)
      time.sleep(0.0625)
    GPIO.output(pins[p], GPIO.LOW)
  time.sleep(1)
  for pp in pins:
    GPIO.output(pp, GPIO.HIGH)

def showReadySequence():
  for p in range(1,6):
    GPIO.output(pins[5 - p], GPIO.LOW)
    time.sleep(0.125)
  for p in range(1,6):
    GPIO.output(pins[5 - p], GPIO.HIGH)
    time.sleep(0.125)
  for rep in range(1,4):
    GPIO.output(pins[0], GPIO.LOW)
    time.sleep(0.0625)
    GPIO.output(pins[0], GPIO.HIGH)
    time.sleep(0.0625)

def showStartSequence():
  # "Standard" drag racing tree is 0.5 sec between lights, but that's
  # kinda slow for a PWD audience to wait each time.
  pace = 0.25  # Time between lights, in seconds.
  for p in range(1,5):
    GPIO.output(pins[p - 1], GPIO.LOW)
    time.sleep(pace)
    GPIO.output(pins[p - 1], GPIO.HIGH)
  GPIO.output(pins[4], GPIO.LOW)
  time.sleep(pace)
  GPIO.output(pins[7], GPIO.LOW)
  time.sleep(1)
  GPIO.output(pins[4], GPIO.HIGH)
  GPIO.output(pins[7], GPIO.HIGH)

# Asynchronously invoked when the START button changes state.
def onSTART(pin):
  if GPIO.input(pin) == 0:
    # Button pressed
    showStartSequence()

# Asynchronously invoked when the READY button on the pole changes state.
def onREADY(pin):
  if GPIO.input(pin) == 0:
    # Button pressed
    showReadySequence()

# Set up all the pins we're using
def startup():
  # Turn off all the relays
  for p in pins:
    GPIO.setup(p, GPIO.OUT, initial=GPIO.HIGH)
  # Set up pushbutton handling
  GPIO.setup(btnREADY, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.add_event_detect(btnREADY, GPIO.BOTH, bouncetime=200,
                        callback=onREADY)
  GPIO.setup(btnSTART, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.add_event_detect(btnSTART, GPIO.BOTH, bouncetime=200,
                        callback=onSTART)
  # Show that we're open for business
  showInitializationSequence()

startup()

try:
  # Any button presses will invoke the event handlers in another thread.  The
  # program will terminate if we just exit the main thread, so instead we have
  # to wait forever in this loop.
  while (1):
    time.sleep(60)
finally:
  GPIO.cleanup()
