#!/usr/bin/python
import RPi.GPIO as GPIO
import sys
import time

GPIO.setmode(GPIO.BCM)

# Relays 1 through 8, in order
# v2
pins = [18, 25, 10, 24, 23, 22, 27, 17]

btnREADY = 9
# btnRESET = 8
btnSTART = 7    

# Returns the GPIO pin number to manipulate.  'pin' is an integer,
# 1-8.
def pin_index(pin):
  try:
    return pins[int(pin) - 1]
  except ValueError:
    print "Unrecognized pin:",pin
    sys.exit(1)

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
  # kinda slow for PWD
  pace = 0.25
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

def onSTART(pin):
  if GPIO.input(pin) == 0:
    showStartSequence()

def onREADY(pin):
  if GPIO.input(pin) == 0:
    showReadySequence()

# Set up all the pins we're using
def startup():
  for p in pins:
    GPIO.setup(p, GPIO.OUT, initial=GPIO.HIGH)
  GPIO.setup(btnREADY, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.add_event_detect(btnREADY, GPIO.BOTH, bouncetime=200,
                        callback=onREADY)
  GPIO.setup(btnSTART, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.add_event_detect(btnSTART, GPIO.BOTH, bouncetime=200,
                        callback=onSTART)
  showInitializationSequence()

startup()
    
try:
  while (1):
    time.sleep(60)
finally:
  GPIO.cleanup()
