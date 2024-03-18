import urllib.request
import urllib.request
from datetime import datetime

import cv2
import numpy as np
import requests
import time


def center_crop(img, new_width, new_height):
    width = img.shape[1]
    height = img.shape[0]

    if new_width is None:
        new_width = min(width, height)

    if new_height is None:
        new_height = min(width, height)

    left = int(np.ceil((width - new_width) / 2))
    right = width - int(np.floor((width - new_width) / 2))

    top = int(np.ceil((height - new_height) / 2))
    bottom = height - int(np.floor((height - new_height) / 2))

    if len(img.shape) == 2:
        center_cropped_img = img[top:bottom, left:right]
    else:
        center_cropped_img = img[top:bottom, left:right, ...]

    return center_cropped_img


def getRemoteImage():
    url = 'http://192.168.178.130:8000/image_shot'  # local IP-adresse
    # url = 'http://78.94.176.119:8000/image_shot'  # Internet IP-adresse

    with urllib.request.urlopen(url) as resp:

        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    return image

def main():

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    cv2.startWindowThread()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    print("________START_______")
    print("Start Time =", current_time)

    URL = 'http://192.168.178.130:8000/motor_init'  # start streaming
    r = requests.get(url=URL)
    # URL = "http://192.168.178.130:8000/move_motor/9" #test todo: delete
    # r = requests.get(url=URL)
    # todo: anschalten
    #  r = requests.get(url=URL)

    bewegungIdentifitiert = True  # todo
    personGefunden = False
    direction = 1
    while (bewegungIdentifitiert):
        time.sleep(0.5)  # 0.3 Sekunden für 18 Grade
        frame = getRemoteImage()

        # image = cv2.imread('./img/pC3.jpg')
        # cv2.waitKey(10)

        cv2.imshow('frame', frame)
        # frame = cv2.resize(frame, (640, 480))

        # using a greyscale picture, also for faster detection

        # detect people in the image
        # returns the bounding boxes for the detected objects
        boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8))

        if len(boxes) > 0:
            personGefunden = True
            print("*******************")
            print(boxes)
            for (x, y, w, h) in boxes:
                print(x, y, w, h)
            print("*******************")
        else:
            personGefunden = False
            print("nobody")
            URL = "http://192.168.178.130:8000/get_kamera_winkel"
            r = requests.get(url=URL)
            print("winkel:", r.text)
            if (int(r.text) == 12 or int(r.text) == 2):
                direction *= -1
            if (direction == 1):
                URL = "http://192.168.178.130:8000/move_right"
            else:
                URL = "http://192.168.178.130:8000/move_left"
            r = requests.get(url=URL)
            time.sleep(0.3)
            continue
        # todo: wandels auf der Suche nach der Persone

        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

        # cv2.imshow('frame', frame)
        cv2.rectangle(frame, (0, 0), (20, 20),
                      (0, 255, 255), 2)
        for (xA, yA, xB, yB) in boxes:
            # display the detected boxes in the colour picture
            cv2.rectangle(frame, (xA, yA), (xB, yB),
                          (0, 255, 0), 2)

            xCenter = (xB + xA) / 2

            Width = frame.shape[1]
            Height = frame.shape[0]  # für 2 Servomotor
            print(Width)
            print("x1:", xA, ", x2: ", xB)
            print("xCenter:", xCenter)
            print("Width / 4:", Width / 4)
            print("_______________")

            URL = "http://192.168.178.130:8000/"
            if (xCenter < Width / 4):
                # move_left
                URL += "move_left"
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)
                print("move left")
            elif (xCenter > 3 * Width / 4):
                # move_right
                URL += "move_right"
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)
                print("move right")
            if 'move' in URL:
                r = requests.get(url=URL)

            cv2.imshow('frame', frame)
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


cv2.destroyAllWindows()

if __name__ == "__main__":
    print("Let's rock!")
    # while(True):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    print("________START_______")
    print("Start Time =", current_time)
    main()
    print("____________________")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Finish Time =", current_time)
