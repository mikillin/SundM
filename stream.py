from flask import Flask, Response, json
import numpy as np
import cv2
import RPi.GPIO as GPIO  # Imports the standard Raspberry Pi GPIO library
from time import sleep
import math

app = Flask(__name__)

global_frame = None
global_winkel = None

# Set up pin 11 for PWM
OUT_PIN = 11
PULSE_FREQ = 50
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)


# Ungefähr 3 Sekunden pro 180 Grade (Wert = 10)
def generate_frames():
    # OpenCV Video Capture
    cap = cv2.VideoCapture(0)  # Change the parameter to the index of the camera

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
        print("The border is reached")



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
    print("move global_winkel = ", str(global_winkel))
    print("move winkel = ", str(winkel))
    global_winkel = int(winkel)

    p = GPIO.PWM(11, 50)  # Sets up pin 11 as a PWM pin
    p.start(0)  # Starts running PWM on the pin and sets it to 0
    p.ChangeDutyCycle(int(winkel))  # Changes the pulse width to winkel (so moves the servo)
    print("delay = ", delay)
    sleep(delay)  ###### hier zu erdenken, was zu tun. ohne Sleep funktioniert Bewegung funktioniert nicht.

    # Clean up everything
    p.stop()  # At the end of the program, stop the PWM

    return getSuccessfullResponse()


@app.route('/json_sensors_state')
def jsonSensorsState():
    data = {
        "parameter1": "value1",
        "parameter2": "value2"
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
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)  # Run the server on port 8000
