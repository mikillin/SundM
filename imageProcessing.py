import cv2
import numpy as np
import urllib.request


def processImage():
    url = 'http://192.168.178.130:8000/image'  # Replace with the URL of your video stream

    with urllib.request.urlopen(url) as resp:
        # read image as an numpy array
        image = np.asarray(bytearray(resp.read()), dtype="uint8")

        # use imdecode function
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # display image
        cv2.imwrite("result.jpg", image)


        HOGCV = cv2.HOGDescriptor()
        HOGCV.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        bounding_box_cordinates, weights = HOGCV.detectMultiScale(image, winStride=(4, 4), padding=(8, 8), scale=1.03)

        person = 1
        for x, y, w, h in bounding_box_cordinates:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, f'person {person}', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            person += 1

        cv2.putText(image, 'Status : Detecting ', (40, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 0, 0), 2)
        cv2.putText(image, f'Total Persons : {person - 1}', (40, 70), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 0, 0), 2)
        cv2.imshow('output', image)
        cv2.imwrite("result_detected.jpg", image)

if __name__ == "__main__":
    processImage()

# http://192.168.178.130:8000/image
