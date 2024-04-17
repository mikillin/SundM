from flask import Flask, Response, json
import numpy as np
import cv2
import RPi.GPIO as GPI
from time import sleep
import math
from datetime import datetime
from gpiozero import LED

app = Flask(__name__)

# globale Variablen
# ein Bild vom Stream
global_frame = None

# Winkel von Servomotoren
global_winkel = None
global_winkel2 = None

# Definition den Pins der Raspberry Pi 3B Platte
OUT_PIN = 11
OUT_PIN_RElAY = 40
PULSE_FREQ = 50
GPIO_TRIGGER = 7
GPIO_ECHO = 12

GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(40, GPIO.OUT)

# Richtung der GPIO-Pins festlegen (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(32, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def distanz():

    GPIO.setmode(GPIO.BOARD)
    GPIO_TRIGGER = 13
    GPIO_ECHO = 12

    GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
    GPIO.setup(GPIO_ECHO, GPIO.IN)
    # setze Trigger auf HIGH
    GPIO.output(GPIO_TRIGGER, True)

    # setze Trigger nach 0.01ms aus LOW
    sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartZeit = datetime.now()
    StopZeit = datetime.now()

    # Startzeit ist gespreichert
    while GPIO.input(GPIO_ECHO) == 0:
        StartZeit = datetime.now()

    # speichere Ankunftszeit
    while GPIO.input(GPIO_ECHO) == 1:
        StopZeit = datetime.now()

    # die Differenz zwischen Start und Ankunft
    TimeElapsed = StopZeit - StartZeit
    # mit der Schallgeschwindigkeit (34300 cm/s) multiplizieren
    # und durch 2 teilen, da hin und zurück
    distanz = (TimeElapsed * 34300) / 2

    return distanz



def generate_frames():
    # OpenCV Funktionalität
    # 0 - die erste Kamera im System
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()  # Read frame from camera
        if not success:
            break
        else:
            global global_frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            data_encode = np.array(buffer)
            byte_encode = data_encode.tobytes()
            global_frame = byte_encode

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/motor_init')
def initMotor():
    global global_winkel

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)

    p = GPIO.PWM(11, 50)  # Sets up pin 11 as a PWM pin
    p.start(0)  # Starts running PWM on the pin and sets it to 0
    cv2.waitKey(0)
    # Move the servo back and forth
    p.ChangeDutyCycle(2)  # Changes the pulse width to 3 (so moves the servo)
    cv2.waitKey(0)
    sleep(4)  # Wait 1 second
    # Clean up everything
    p.stop()  # At the end of the program, stop the PWM
    GPIO.cleanup()
    global_winkel = 0
    return getSuccessfullResponse()


@app.route('/image_shot')
def imageShot():
    return global_frame


@app.route('/get_kamera_winkel')
def getCurrentPosition():

    global global_winkel

    return str(global_winkel)


@app.route('/move_right')
def moveMotorRight():

    global global_winkel

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)

    if global_winkel < 12:
        global_winkel += 1
    else:
        global_winkel = 12
        print("Die Grenze ist erreicht")

    p = GPIO.PWM(11, 50)  # Sets up pin 11 as a PWM pin
    p.start(0)  # Starts running PWM on the pin and sets it to 0
    cv2.waitKey(0)
    # Move the servo back and forth
    p.ChangeDutyCycle(global_winkel)  # Changes the pulse width to 3 (so moves the servo)
    cv2.waitKey(0)
    sleep(0.5)  # Wait 1 second
    # Clean up everything
    p.stop()  # At the end of the program, stop the PWM
    GPIO.cleanup()

    return getSuccessfullResponse()


@app.route('/move_left')
def moveMotorLeft():
    global global_winkel

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)

    if global_winkel > 2:
        global_winkel -= 1
        print("The border is reached")
    else:
        global_winkel = 2

    p = GPIO.PWM(11, 50)  # Sets up pin 11 as a PWM pin
    p.start(0)  # Starts running PWM on the pin and sets it to 0
    cv2.waitKey(0)
    # Move the servo back and forth
    p.ChangeDutyCycle(global_winkel)  # Changes the pulse width to 3 (so moves the servo)
    cv2.waitKey(0)
    sleep(0.5)
    # Clean up everything
    p.stop()  # At the end of the program, stop the PWM
    GPIO.cleanup()

    return getSuccessfullResponse()


@app.route('/move_motor/<winkel>')
def moveMotor(winkel):
    global global_winkel

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)

    # Grad  - Funktion
    #
    # 0 - servo1.ChangeDutyCycle(2)
    # 180 - servo1.ChangeDutyCycle(12)

    delay = math.ceil(((abs(int(global_winkel) - int(winkel))) * 0.3))
    if delay < 0.5:
        delay = 0.5

    global_winkel = int(winkel)

    p = GPIO.PWM(11, 50)  # Sets up pin 11 as a PWM pin
    p.start(0)  # Starts running PWM on the pin and sets it to 0
    p.ChangeDutyCycle(int(winkel))  # Changes the pulse width to winkel (so moves the servo)
    print("delay = ", delay)
    sleep(delay)  ###### hier zu erdenken, was zu tun. ohne Sleep funktioniert Bewegung funktioniert nicht.

    # Clean up everything
    p.stop()  # At the end of the program, stop the PWM

    return getSuccessfullResponse()

# für 2 Servomotor
@ app.route('/move_motor2/<winkel>')
def moveMotor2(winkel):
    global global_winkel2

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(15, GPIO.OUT)

    delay = math.ceil(((abs(int(global_winkel) - int(winkel))) * 0.3))
    if delay < 0.5:
        delay = 0.5

    global_winkel2 = int(winkel)

    p = GPIO.PWM(15, 50)  # Sets up pin 11 as a PWM pin
    p.start(0)  # Starts running PWM on the pin and sets it to 0
    p.ChangeDutyCycle(int(winkel))  # Changes the pulse width to winkel (so moves the servo)

    sleep(delay)  ###### hier zu erdenken, was zu tun. ohne Sleep funktioniert Bewegung funktioniert nicht.
    p.stop()  # am Ende muss PWM gestoppt werden

    return getSuccessfullResponse()

@app.route('/rote_led')
def rote_led():

    roteled = LED("GPIO21")
    roteled.on()
    sleep(1)
    roteled.off()

    return getSuccessfullResponse()


@app.route('/gruene_led')
def gruene_led():

    grüneled = LED("GPIO20")
    grüneled.on()
    sleep(1)
    grüneled.off()

    return getSuccessfullResponse()


@app.route('/gelbe_led')
def gelbe_led():

    gelbeled = LED("GPIO16")
    gelbeled.on()
    sleep(1)
    gelbeled.off()

    return getSuccessfullResponse()


@app.route('/json_sensors_state')
def jsonSensorsState():

    distaz_ = str(distanz())
    data = {
        "distanz": distaz_,
        "winkel": global_winkel
    }

    return json.dumps(data)


@app.route('/')
def index():
    initMotor()
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def getSuccessfullResponse():

    return app.response_class(
        response=json.dumps({"status": "success", "code": 0}),
        status=200,
        mimetype='application/json'
    )


if __name__ == "__main__":
    initMotor()
    generate_frames()

    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
