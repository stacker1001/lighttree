#!/usr/bin/python
from fastapi import FastAPI, BackgroundTasks
from fastapi_utils.tasks import repeat_every
import RPi.GPIO as GPIO
import sys
import time
import os
import logging
import pyttsx3

logger = logging.getLogger(__name__)

app = FastAPI()
try:
  engine = pyttsx3.init(driverName='espeak', debug=True)
except Exception as e:
  logging.error(str(e))

GPIO.setmode(GPIO.BCM)

# Relays 1 through 8, in order.  These are active-LOW pins, i.e., sending a LOW
# output turns on the corresponding relay, and sending a HIGH turns off the
# relay.
#pins = [18, 25, 10, 24, 23, 22, 27, 17]
pins = [26, 6, 13, 5, 12, 24]

# These are the two hardware pushbutton inputs; the input will show 0 if the
# button is pressed, 1 if it's not.
#
# "READY" button on post
btnREADY = 23
ledREADY = 25
# Actual start buttons
btnSTART1 = 4
btnSTART2 = 17
# Out to Track
outSTART1 = 27
outSTART2 = 22

status = 'INITIALIZING'
race_mode = 'DERBY'
ready_press_time = 0
drag_start_time = 0
false_start = False

#RuntimeWarning: This channel is already in use, continuing anyway.
#Use GPIO.setwarnings(False) to disable warnings.
GPIO.setwarnings(False)

@app.get("/show/sequence/initialization")
def showInitializationSequence():
  try:
    logger.info('Showing Initialization Sequence')
    for rep in range(3):
      GPIO.output(pins[0], GPIO.LOW)
      GPIO.output(pins[1], GPIO.LOW)
      time.sleep(0.0625)
      GPIO.output(pins[0], GPIO.HIGH)
      GPIO.output(pins[1], GPIO.HIGH)
      time.sleep(0.0625)
    GPIO.output(pins[0], GPIO.LOW)
    GPIO.output(pins[1], GPIO.LOW)
    for p in range(2, 6):
      for rep in range(3):
        GPIO.output(pins[p], GPIO.LOW)
        time.sleep(0.0625)
        GPIO.output(pins[p], GPIO.HIGH)
        time.sleep(0.0625)
      GPIO.output(pins[p], GPIO.LOW)
    time.sleep(1)
    for p in pins:
      GPIO.output(p, GPIO.HIGH)
    return {"sequence": "initialization"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/switch_race_modes")
def showSwitchRaceModesSequence():
  try:
    logger.info('Showing Switch Race Modes Sequence')
    for p in pins:
      GPIO.output(p, GPIO.LOW)
    time.sleep(0.5)
    for p in pins:
      GPIO.output(p, GPIO.HIGH)    
    return {"sequence": "switch_race_modes"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/ready")
def showReadySequence():
  try:
    logger.info('Showing Ready Sequence')
    for p in range(5, 1, -1):
      GPIO.output(pins[p], GPIO.LOW)
      time.sleep(0.125)
    GPIO.output(pins[0], GPIO.LOW)
    GPIO.output(pins[1], GPIO.LOW)
    time.sleep(0.125)
    for p in range(5, 1, -1):
      GPIO.output(pins[p], GPIO.HIGH)
      time.sleep(0.125)
    GPIO.output(pins[0], GPIO.HIGH)
    GPIO.output(pins[1], GPIO.HIGH)
    time.sleep(0.125)      
    for rep in range(3):
      GPIO.output(pins[0], GPIO.LOW)
      GPIO.output(pins[1], GPIO.LOW)
      time.sleep(0.0625)
      GPIO.output(pins[0], GPIO.HIGH)
      GPIO.output(pins[1], GPIO.HIGH)
      time.sleep(0.0625)
    engine.say("Ready")
    engine.runAndWait()
    return {"sequence": "ready"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/derby_start")
def showDerbyStartSequence():
  try:
    logger.info('Showing Derby Start Sequence')
    pace = 0.25  # Time between lights, in seconds.
    GPIO.output(pins[0], GPIO.LOW)
    GPIO.output(pins[1], GPIO.LOW)
    time.sleep(pace)
    GPIO.output(pins[0], GPIO.HIGH)
    GPIO.output(pins[1], GPIO.HIGH)
    for p in range(2, 6):
      GPIO.output(pins[p], GPIO.LOW)
      time.sleep(pace)
      GPIO.output(pins[p], GPIO.HIGH)
    GPIO.output(pins[5], GPIO.LOW)
    time.sleep(pace)
    GPIO.output(outSTART1, GPIO.LOW)
    time.sleep(1)
    GPIO.output(pins[5], GPIO.HIGH)
    GPIO.output(outSTART1, GPIO.HIGH)
    return {"derby_sequence": "start"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/drag_start")
def showDragStartSequence():
  global status
  global drag_start_time
  try:
    logger.info('Showing Drag Start Sequence')
    pace = 0.5  # Time between lights, in seconds.
    if status != 'DRAG_FALSE_START':
      GPIO.output(pins[0], GPIO.LOW)
      GPIO.output(pins[1], GPIO.LOW)
      time.sleep(pace)
      GPIO.output(pins[0], GPIO.HIGH)
      GPIO.output(pins[1], GPIO.HIGH)
    for p in range(2, 5):
      if status != 'DRAG_FALSE_START':
        GPIO.output(pins[p], GPIO.LOW)
        time.sleep(pace)
        GPIO.output(pins[p], GPIO.HIGH)
    if status != 'DRAG_FALSE_START':
      logger.info('Drag Race Started')
      GPIO.output(pins[5], GPIO.LOW)
      status = 'DRAG_RACING'
      drag_start_time = time.time()
    return {"drag_sequence": "start"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

@app.get("/show/sequence/shutdown")
def showShutdownSequence():
  try:
    logger.info('Showing Shutdown Sequence')
    for p in pins:
      GPIO.output(p, GPIO.LOW)
    time.sleep(0.5)  
    GPIO.output(pins[0], GPIO.HIGH)
    GPIO.output(pins[1], GPIO.HIGH)
    for p in range(2, 6):
      time.sleep(0.5)
      GPIO.output(pins[p], GPIO.HIGH)
    return {"sequence": "shutdown"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

def false_start(racer):
  global status
  try:
    logger.info('False Start Racer {}'.format(racer))
    status = 'DRAG_FALSE_START'
    GPIO.output(pins[racer - 1], GPIO.LOW)
    track_not_ready()
    engine.say('False Start Racer {}'.format(racer))
    engine.runAndWait()
  except Exception as e:
    logging.error(str(e))  

@app.get("/button/start1")
def onSTART1_api():
  try:
    onSTART1(btnSTART1, True)
    return {"button": "start1"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

# Asynchronously invoked when the START1 button changes state.
def onSTART1(pin, api = False):
  global status
  try:
    pin = int(pin)
    if (GPIO.input(pin) == GPIO.LOW) or api:
      # Button pressed
      logger.info('Start1 Button Pressed')
      if race_mode == 'DERBY':
        if status == 'DERBY_READY':
          logger.info('Starting Race')
          GPIO.remove_event_detect(btnSTART1)
          showDerbyStartSequence()
          status = 'DERBY_RACING'
        else:
          logger.info('Track not Ready')
      elif race_mode == 'DRAG':
        if status == 'DRAG_RACING':
          logger.info('Racer 1 Started')
          GPIO.remove_event_detect(btnSTART1)
          GPIO.output(outSTART1, GPIO.LOW)
        elif status == 'DRAG_START':
          false_start(1)
      else:
        logging.error('Invalid Race Mode')
  except Exception as e:
    logging.error(str(e))

@app.get("/button/start2")
def onSTART2_api():
  try:
    onSTART2(btnSTART2, True)
    return {"button": "start2"}
  except Exception as e:
    logging.error(str(e))
    return {"error": str(e)}

# Asynchronously invoked when the START2 button changes state.
def onSTART2(pin, api = False):
  global status
  try:
    pin = int(pin)
    if (GPIO.input(pin) == GPIO.LOW) or api:
      # Button pressed
      logger.info('Start2 Button Pressed')
      if race_mode == 'DERBY':
        logger.info('Button 2 Not Used in DERBY Mode')
      elif race_mode == 'DRAG':
        if status == 'DRAG_RACING':
          logger.info('Racer 2 Started')
          GPIO.remove_event_detect(btnSTART2)
          GPIO.output(outSTART2, GPIO.LOW)
        elif status == 'DRAG_START':
          false_start(2)
      else:
        logging.error('Invalid Race Mode')
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

# Asynchronously invoked when the READY button on the pole changes state.
def onREADY(pin, api = False):
  global ready_press_time
  global status
  logger.info('Ready Button State: {}'.format(GPIO.input(pin)))
  try:
    if (ready_press_time == 0) and ((GPIO.input(pin) == GPIO.LOW) or api):
      logger.info('Ready Button Pressed')
      ready_press_time = time.time()
      if race_mode == 'DERBY':
        if status != 'DERBY_READY':
          logger.info('Track getting ready')
          showReadySequence()
          GPIO.add_event_detect(btnSTART1, GPIO.BOTH, bouncetime=1000, callback=onSTART1)
          status = 'DERBY_READY'
          logger.info('Track ready')
        else:
          logger.info('Track already ready')
      elif race_mode == 'DRAG':
        #drag_reset()
        if status != 'DRAG_FALSE_START':
          logger.info('Drag race starting')
          GPIO.add_event_detect(btnSTART1, GPIO.BOTH, bouncetime=1000, callback=onSTART1)
          GPIO.add_event_detect(btnSTART2, GPIO.BOTH, bouncetime=1000, callback=onSTART2)
          status = 'DRAG_START'
        else:
          logger.info('Clearing False Start')
          engine.say('False Start Cleared.')
          engine.runAndWait()
          drag_reset()
      else:
        logging.error('Invalid Race Mode')
    elif GPIO.input(pin) == GPIO.HIGH:
      # Button released, cancel timing how long it was held
      logger.info('Ready Button Released')
      ready_press_time = 0
    # else ignore apparent button "press" while already held
  except Exception as e:
    logging.error(str(e))

@app.on_event('startup')
@repeat_every(seconds=.5, logger=logger, raise_exceptions=True)
def long_press():
  global ready_press_time
  try:
    #logger.info('ready_press_time = {0}'.format(ready_press_time))
    if (ready_press_time != 0) and (GPIO.input(btnREADY) == GPIO.LOW):
      ready_hold_duration = time.time() - ready_press_time
      logger.info('ready_hold_duration = {0}'.format(ready_hold_duration))
      if (ready_hold_duration > 7.0) and (status != 'SHUTTING-DOWN'):
        shutdown()
        #ready_press_time = 0
      elif (ready_hold_duration > 3.0) and (status != 'SWITCHING-MODES'):
        switch_race_modes()
        #ready_press_time = 0
    else:
      ready_press_time = 0
  except Exception as e:
    logging.error(str(e))

def drag_reset():
  global drag_start_time
  global status

  try:
    logger.info('Race over. Resetting')
    for p in pins:
      GPIO.output(p, GPIO.HIGH)
    GPIO.output(outSTART1, GPIO.HIGH)
    GPIO.output(outSTART2, GPIO.HIGH)
    track_not_ready()
    drag_start_time = 0
    status = 'DRAG_READY'
    engine.say('Ready To Race')
    engine.runAndWait()
  except Exception as e:
    logging.error(str(e))

@app.on_event('startup')
@repeat_every(seconds=.5, logger=logger, raise_exceptions=True)
def drag_loop():
  global status
  global drag_start_time
  try:
    if race_mode == 'DRAG':
      #logger.info('drag_loop')
      if status == 'DRAG_START':
        showDragStartSequence()
      elif status == 'DRAG_RACING':
        drag_race_duration = time.time() - drag_start_time
        if drag_race_duration > 10.0:
          drag_reset()

  except Exception as e:
    logging.error(str(e))

@app.get("/shutdown")
def shutdown():
  global status
  try:
    logger.info('Shutting Down Gracefully')
    track_not_ready()
    engine.say("Shutting Down")
    engine.runAndWait()
    status = 'SHUTTING-DOWN'
    showShutdownSequence()
    os.system("shutdown -h now")
  except Exception as e:
    logging.error(str(e))

@app.on_event('shutdown')
def cleanup():
  try:
    GPIO.cleanup()
  except Exception as e:
    logging.error(str(e))

@app.get("/switch_race_mode")
def switch_race_modes():
  global race_mode
  global status
  try:
    if (race_mode == 'DERBY'):
      race_mode = 'DRAG'
    else:
      race_mode = 'DERBY'
    status = 'SWITCHING-MODES'
    track_not_ready()
    logger.info('Switching Race Mode to {}'.format(race_mode))
    showSwitchRaceModesSequence()  
    engine.say("Mode is {}".format(race_mode))
    engine.say("Let's Race")
    engine.runAndWait()
  except Exception as e:
    logging.error(str(e))

def track_not_ready():

  try:
    GPIO.remove_event_detect(btnSTART1)
    GPIO.remove_event_detect(btnSTART2)
  except Exception as e:
    logging.error(str(e))    


# Set up all the pins we're using
def startup():
  try:
    logger.info('Starting LightTree')
    # Turn off all the relays
    for p in pins:
      GPIO.setup(p, GPIO.OUT, initial=GPIO.HIGH)
    # Set up RESET LED
    GPIO.setup(ledREADY, GPIO.OUT, initial=GPIO.HIGH)
    # Set up track outputs
    GPIO.setup(outSTART1, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(outSTART2, GPIO.OUT, initial=GPIO.HIGH)
    # Set up pushbutton handling
    GPIO.setup(btnREADY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(btnREADY, GPIO.BOTH, bouncetime=1000, callback=onREADY)
    #GPIO.setup(btnSTART1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(btnSTART1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #GPIO.add_event_detect(btnSTART1, GPIO.BOTH, bouncetime=1000, callback=onSTART1)
    GPIO.setup(btnSTART2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #GPIO.add_event_detect(btnSTART2, GPIO.BOTH, bouncetime=1000, callback=onSTART2)
    
    # Show that we're open for business
    showInitializationSequence()
    engine.say("Mode is {}".format(race_mode))
    engine.say("Let's Race")
    engine.runAndWait()
  except Exception as e:
    logging.error(str(e))

startup()


##try:
  # Any button presses will invoke the event handlers in another thread.  The
  # program will terminate if we just exit the main thread, so instead we have
  # to wait forever in this loop.
##  while (1):
##    time.sleep(1)
##    if ready_press_time != 0:
##      ready_hold_duration = time.time() - ready_press_time
##      if ready_hold_duration > 5.0:
##        showShutdownSequence()
##        os.system("shutdown -h now")
##        ready_press_time = 0
##finally:
##  GPIO.cleanup()
