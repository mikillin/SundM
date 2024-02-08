import cv2
import requests
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


if __name__ == "__main__":
    processImage()

# http://192.168.178.130:8000/image
