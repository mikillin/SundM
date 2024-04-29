from flask import Flask, Response, json
import numpy as np
import cv2
import RPi.GPIO as GPIO
from time import sleep
import math
from datetime import datetime
from gpiozero import LED

# Definition der Web-Applikation
app = Flask(__name__)

# globale Variablen
# ein Bild vom Videostream
global_frame = None
# Winkel vom Servomotor
global_winkel = None

# Einstellungen für den Pins der Raspberry Pi 3B Platte
PULSE_FREQ_SERVO = 50
GPIO_PIR = 23
GPIO_ECHO_TRIGGER = 13
GPIO_ECHO = 12
GPIO_SERVO = 11
GPIO_TRIGGER = 7

# Einstellungen für Servomotor
WINKEL_MAX_WERT = 12
WINKEL_MIN_WERT = 2
DIE_DAUER_FÜR_SERVOMOTOR_ZU_DREHEN_1_MAL_MIT_ABWEIHUNGEN = 0.5
DIE_DAUER_FÜR_SERVOMOTOR_ZU_DREHEN_1_MAL = 0.3

# Einstellungen für den Pins der Raspberry Pi 3B Platte für LEDs
GPIO_LED_ROT = "GPIO21"
GPIO_LED_GRUEN = "GPIO20"
GPIO_LED_GELB = "GPIO16"
DAUER_FUER_LED_BLINKEN_IN_SEKUNDEN = 1


# REST-API-Funktion initialisiert die Variabel "global_winkel"
# und setzt den Servomotor auf 0 Grade ein
@app.route('/motor_init')
def initMotor():
    global global_winkel

    # Initialisierung  der Variable "global_winkel" als maximal möglicher dafür Wert
    global_winkel = WINKEL_MAX_WERT

    # Der Servomotor muss  nach Links bis zum Ende sich drehen.
    return moveMotor(WINKEL_MIN_WERT)


# REST-API-Funktion schickt ein Bild von der Videostream ab
@app.route('/image_shot')
def imageShot():
    return global_frame


# REST-API-Funktion schickt den Wert vom Winkel von der Kamera ab
@app.route('/get_camera_angle')
def getCurrentPosition():
    global global_winkel

    return str(global_winkel)


# REST-API-Funktion dreht einmal den Servomotor rechts
@app.route('/move_right')
def moveMotorRight():
    global global_winkel

    if global_winkel < WINKEL_MAX_WERT:
        global_winkel += 1
    else:
        global_winkel = WINKEL_MAX_WERT
        print("log: Die Grenze ist erreicht")

    return moveMotor(global_winkel)


# REST-API-Funktion dreht einmal den Servomotor links
@app.route('/move_left')
def moveMotorLeft():
    global global_winkel

    if global_winkel > WINKEL_MIN_WERT:
        global_winkel -= 1
        print("log: Die Grenze ist erreicht")
    else:
        global_winkel = WINKEL_MIN_WERT

    return moveMotor(global_winkel)


# REST-API-Funktion schick den Zustand des Bewegungssensors ab
@app.route('/isvisited')
def istBewegt():
    return str(GPIO.input(GPIO_PIR))


# REST-API-Funktion dreht den Servomotor auf 18 Grade/1 Mal
@app.route('/move_motor/<winkel>')
def moveMotor(winkel):
    global global_winkel

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(GPIO_SERVO, GPIO.OUT)

    # Grad  - Funktion
    #
    # 0 - servo.ChangeDutyCycle(2)
    # 180 - servo.ChangeDutyCycle(12)

    delay = math.ceil(((abs(int(global_winkel) - int(winkel))) * DIE_DAUER_FÜR_SERVOMOTOR_ZU_DREHEN_1_MAL))
    if delay < DIE_DAUER_FÜR_SERVOMOTOR_ZU_DREHEN_1_MAL_MIT_ABWEIHUNGEN:
        delay = DIE_DAUER_FÜR_SERVOMOTOR_ZU_DREHEN_1_MAL_MIT_ABWEIHUNGEN

    global_winkel = int(winkel)
    p = GPIO.PWM(GPIO_SERVO, PULSE_FREQ_SERVO)
    p.start(0)
    p.ChangeDutyCycle(int(winkel))

    sleep(delay)

    # Am Ende der Methode muss PWM gestoppt werden
    p.stop()

    return getSuccessfullResponse()


# REST-API-Funktion schaltet das rote LED für 1 Sekunde an
@app.route('/red_led')
def rote_led():
    led_anschalten(GPIO_LED_ROT)

    return getSuccessfullResponse()


# REST-API-Funktion schaltet das gruene LED für 1 Sekunde an
@app.route('/green_led')
def gruene_led():
    led_anschalten(GPIO_LED_GRUEN)

    return getSuccessfullResponse()


# REST-API-Funktion schaltet das gelbe LED für 1 Sekunde an
@app.route('/yellow_led')
def gelbe_led():
    led_anschalten(GPIO_LED_GELB)

    return getSuccessfullResponse()


# REST-API-Funktion erfasst die Zustände von Sensoren als json
@app.route('/json_sensors_state')
def jsonSensorsState():
    global global_winkel

    distaz_ = str(distanz())
    data = {
        "distance": distaz_,
        "angle": global_winkel
    }

    return json.dumps(data)


# REST-API-Funktion startet den Videostrem
@app.route('/')
def index():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# die Funktion schaltet LED für einen bestimmten Zeitraum (1 Sekunde) an
def led_anschalten(typ):
    led = LED(typ)
    led.on()
    sleep(DAUER_FUER_LED_BLINKEN_IN_SEKUNDEN)
    led.off()


# die Funktion generiert den erfolgreichen Status für REST-Responses
def getSuccessfullResponse():
    return app.response_class(
        response=json.dumps({"status": "success", "code": 0}),
        status=200,
        mimetype='application/json'
    )


# die Funktion kalkuliert die Distanz von Ultraschallsensor bis zum Ziel
def distanz():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(GPIO_ECHO, GPIO.IN)

    GPIO.setup(GPIO_ECHO_TRIGGER, GPIO.OUT)

    #  Trigger wird zuerst als HOCH initialisiert
    GPIO.output(GPIO_ECHO_TRIGGER, True)

    # Trigger wird nach 0.01ms als NIEDRIG initialisiert
    sleep(0.00001)
    GPIO.output(GPIO_ECHO_TRIGGER, False)

    StartZeit = datetime.now()
    StopZeit = datetime.now()

    # Startzeit ist gespeichert
    while GPIO.input(GPIO_ECHO) == 0:
        StartZeit = datetime.now()

    # Ankunftszeit ist gespeichert
    while GPIO.input(GPIO_ECHO) == 1:
        StopZeit = datetime.now()

    # Kalkulation der Differenz zwischen Start- und Ankunftszeit
    TimeElapsed = StopZeit - StartZeit
    # Die Distanz ist kalkuliert, als die Schallgeschwindigkeit (34300 cm/s) muss mit dem Zeitraum multipliziert
    # und danach durch 2 geteilt werden, da hin und zurück bewegt sich der Signal
    distanz = (TimeElapsed * 34300) / 2

    return distanz


# die Funktion generiert den Videostream
def generate_frames():
    # OpenCV Funktionalität
    # 0 - die erste Kamera im System
    cap = cv2.VideoCapture(0)

    while True:
        # Auslesen des Bildes aus Videostream
        success, frame = cap.read()
        if not success:
            break
        else:
            global global_frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Dekodieren den Bytes des Bildes
            data_encode = np.array(buffer)
            byte_encode = data_encode.tobytes()
            global_frame = byte_encode

            # Dekodieren des Bildes als jpeg-Datei
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Funktion startet den Algorithmen
if __name__ == "__main__":
    # initialisierung des Servomotors
    initMotor()

    #Start des Videostreames
    generate_frames()

    #Start der Web-Anwendung
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
