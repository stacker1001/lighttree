#!/usr/bin/python
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import RPi.GPIO as GPIO
import sys
import time
import os
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

GPIO.setmode(GPIO.BCM)

# Relays 1 through 8, in order.  These are active-LOW pins, i.e., sending a LOW
# output turns on the corresponding relay, and sending a HIGH turns off the
# relay.
#pins = [18, 25, 10, 24, 23, 22, 27, 17]
pins = [26, 6, 13, 5, 12]

# These are the two hardware pushbutton inputs; the input will show 0 if the
# button is pressed, 1 if it's not.
#
# "READY" button on post
btnREADY = 23
ledREADY = 25
# Actual start buttons
btnSTART1 = 4
btnSTART2 = 27
# Out to Track
outSTART1 = 24
#outSTART2 = 0

status = 'INITIALIZING'

#RuntimeWarning: This channel is already in use, continuing anyway.
#Use GPIO.setwarnings(False) to disable warnings.
GPIO.setwarnings(False)

@app.get("/show/sequence/initialization")
def showInitializationSequence():
  try:
    logger.info('Showing Initialization Sequence')
    for p in range(0, 5):
      for rep in range(1,4):
        GPIO.output(pins[p], GPIO.HIGH)
        time.sleep(0.0625)
        GPIO.output(pins[p], GPIO.LOW)
        time.sleep(0.0625)
      GPIO.output(pins[p], GPIO.HIGH)
    time.sleep(1)
    for pp in pins:
      GPIO.output(pp, GPIO.LOW)
    return {"sequence": "initialization"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/ready")
def showReadySequence():
  try:
    logger.info('Showing Ready Sequence')
    for p in range(1,6):
      GPIO.output(pins[5 - p], GPIO.HIGH)
      time.sleep(0.125)
    for p in range(1,6):
      GPIO.output(pins[5 - p], GPIO.LOW)
      time.sleep(0.125)
    for rep in range(1,4):
      GPIO.output(pins[0], GPIO.HIGH)
      time.sleep(0.0625)
      GPIO.output(pins[0], GPIO.LOW)
      time.sleep(0.0625)
    return {"sequence": "ready"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/start")
def showStartSequence():
  # "Standard" drag racing tree is 0.5 sec between lights, but that's
  # kinda slow for a PWD audience to wait each time.
  try:
    logger.info('Showing Start Sequence')
    pace = 0.25  # Time between lights, in seconds.
    for p in range(1,5):
      GPIO.output(pins[p - 1], GPIO.HIGH)
      time.sleep(pace)
      GPIO.output(pins[p - 1], GPIO.LOW)
    GPIO.output(pins[4], GPIO.HIGH)
    time.sleep(pace)
    GPIO.output(outSTART1, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(pins[4], GPIO.LOW)
    GPIO.output(outSTART1, GPIO.LOW)
    return {"sequence": "start"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/shutdown")
def showShutdownSequence():
  try:
    logger.info('Showing Shutdown Sequence')
    for pp in pins:
      GPIO.output(pp, GPIO.HIGH)
    for p in range(0, 5):
      time.sleep(0.5)
      GPIO.output(pins[p], GPIO.LOW)
    return {"sequence": "shutdown"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/button/start")
def onSTART_api():
  try:
    onSTART(btnSTART1, True)
    return {"button": "start"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}


# Asynchronously invoked when the START button changes state.
def onSTART(pin, api = False):
  global status
  try:
    pin = int(pin)
    if (GPIO.input(pin) == 0) or api:
      # Button pressed
      logger.info('Start Button Pressed')
      if status == 'READY':
        logger.info('Starting Race')
        showStartSequence()
        status = 'RACING'
      else:
        logger.info('Track not Ready')
  except Exception as e:
    logging.error(str(e))

@app.get("/button/ready")
def onREADY_api():
  try:
    onREADY(btnREADY, True)
    return {"button": "ready"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}
  
ready_press = 0
# Asynchronously invoked when the READY button on the pole changes state.
def onREADY(pin, api = False):
  global ready_press
  global status
  try:
    if (ready_press == 0) and ((GPIO.input(pin) == 0) or api):
      logger.info('Ready Button Pressed')
      ready_press = time.time()
      showReadySequence()
      status = 'READY'
    elif GPIO.input(pin) == 1:
      # Button released, cancel timing how long it was held
      logger.info('Ready Button Released')
      ready_press = 0
    # else ignore apparent button "press" while already held
  except Exception as e:
    logging.error(str(e))

@app.on_event('startup')
@repeat_every(seconds=1, logger=logger, raise_exceptions=True)
def long_press():
  global ready_press
  global btnREADY
  try:
    #logger.info('ready_press = {0}'.format(ready_press))
    if (ready_press != 0) and (GPIO.input(btnREADY) == 0):
      howlong = time.time() - ready_press
      if (howlong > 5.0) and (status != 'SHUTTING-DOWN'):
        shutdown()
        #ready_press = 0
    else:
      ready_press = 0
  except Exception as e:
    logging.error(str(e))

@app.get("/shutdown")
def shutdown():
  global status
  try:
    logger.info('Shutting Down Gracefully')
    showShutdownSequence()
    status = 'SHUTTING-DOWN'
    os.system("shutdown -h now")
  except Exception as e:
    logging.error(str(e))

@app.on_event('shutdown')
def GPIO_cleanup():
  try:
    GPIO.cleanup()
  except Exception as e:
    logging.error(str(e))

# Set up all the pins we're using
def startup():
  try:
    logger.info('Starting LightTree')
    # Turn off all the relays
    for p in pins:
      GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
    # Set up RESET LED
    GPIO.setup(ledREADY, GPIO.OUT, initial=GPIO.HIGH)
    # Set up track outputs
    GPIO.setup(outSTART1, GPIO.OUT, initial=GPIO.LOW)
    #GPIO.setup(outSTART2, GPIO.OUT, initial=GPIO.LOW)
    # Set up pushbutton handling
    GPIO.setup(btnREADY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(btnREADY, GPIO.FALLING, bouncetime=300, callback=onREADY)
    #GPIO.setup(btnSTART1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btnSTART1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(btnSTART1, GPIO.RISING, bouncetime=300, callback=onSTART)
  #  GPIO.setup(btnSTART2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  #  GPIO.add_event_detect(btnSTART2, GPIO.BOTH, bouncetime=200, callback=onSTART)
    # Show that we're open for business
    showInitializationSequence()
  except Exception as e:
    logging.error(str(e))

startup()


##try:
  # Any button presses will invoke the event handlers in another thread.  The
  # program will terminate if we just exit the main thread, so instead we have
  # to wait forever in this loop.
##  while (1):
##    time.sleep(1)
##    if ready_press != 0:
##      howlong = time.time() - ready_press
##      if howlong > 5.0:
##        showShutdownSequence()
##        os.system("shutdown -h now")
##        ready_press = 0
##finally:
##  GPIO.cleanup()
