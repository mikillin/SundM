# iportieren notwendige Bbliotheken
import urllib.request
import urllib.request

import cv2
import face_recognition
import numpy as np
import requests
import time


# zu erhalten das Bild vom EDGE-Gerät
def getRemoteImage():
    # die Definition von der IP-Adresse des EDGE-Geräts
    # die IP-Adresse kann lokal sein, sowie aus dem Internet
    url = 'http://172.20.10.2:8000/image_shot'  # locale IP-Adresse
    # url = 'http://78.94.176.119:8000/image_shot'  #statische Internet IP-Adresse

    # zu erhalten dsa Bild vom Response und das Bild passen zu formatieren
    with urllib.request.urlopen(url) as resp:
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    return image


# Die Hauptmethode
def main():
    # das Foto vom Besizer zu definieren
    owner_image = face_recognition.load_image_file("owner.png")

    # Merkmale zu dekodieren vom Foto des Besitzers
    owner_face_encoding = face_recognition.face_encodings(owner_image)[0]

    # Wenn viele Besizer es gibt, können alle Fotos hinzugefügt werden
    known_face_encodings = [
        owner_face_encoding
    ]
    # den entsprechenden Namen zu definieren
    known_face_names = [
        "Owner"
    ]

    # die Inizializsation des HOG Descriptor
    hog = cv2.HOGDescriptor()

    # die Inizialization des SVM-Detektors auf dem Grund von HOG Descriptor
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # zu Starten eine neue Thread, um viele Clients zusammenarbeiten zu können
    cv2.startWindowThread()

    # zu INzialisiren den Servomotor
    URL = 'http://172.20.10.2:8000/motor_init'  # start streaming

    # zu ausführen den REST-Request
    r = requests.get(url=URL)

    # wiel keine Persnonen erkennt sein, muss die Program 1 Sekunde warten und danach wieder die Operation requestieren
    bewegungIdentifitiert = True  # todo

    ## jemand ist erkannt

    # zuerst müssen die Kameras von Links nach rechts sich bewegen
    direction = 1

    while (bewegungIdentifitiert):

        # abhängig von Servomotor abzuwarten, wenn der motor die bewegung ducrhgeführt haben wird
        time.sleep(0.5)  # 0.3 Sekunden für 18 Grade

        # zu erhalten das Foto vom Kamera
        frame = getRemoteImage()

        # zu speichern das Foto aufm Speicherakrte
        cv2.imwrite("image.jpg", frame)
        # abwarten, um die opertaion bis zum Ende fertig gemach zu können
        time.sleep(0.5)

        # zu zeigen das Foto aufm bildschirm
        cv2.imshow("frame", frame)

        ##Gisichtserkennung
        # zu ändern das Foto in dem Richtigen Format
        rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])

        # zu finden die Positionen des Gesichtes
        face_locations = face_recognition.face_locations(rgb_frame)

        # zu erncodieren des erkannten Gesichten
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Jedes Gesicht zu bearbeiten
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # die Nitialisaion des Names der arkennten Person
            name = "Unknown"
            # zu finden bekannte Gesichte
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            # zufinden dias Gesicht, dass Ähnlich ambestens dem bekannten GEsciht
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            # jemand ist anerkannt
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                # die Person ist als "Owner" eingegeben
                if name == "Owner":
                    #zu schiekne request grüne LED zu erzeigen
                    URL = 'http://172.20.10.2:8000/gruene_led'  # start streaming
                    r = requests.get(url=URL)
            else:
                # zu schiekne request rote LED zu erzeigen
                URL = 'http://172.20.10.2:8000/rote_led'  # start streaming
                r = requests.get(url=URL)

            # hinzuzfügen die Rahmen auf dem Gesicht auf dem Bild
            cv2.rectangle(frame, (left - 50, top - 50), (right + 50, bottom + 50), (0, 0, 255), 2)

            # hinzuzfügen den Namen auf dem Bild
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            # zu definieren den Schreift für die ANschreibungen
            font = cv2.FONT_HERSHEY_DUPLEX
            # hinzuzufügen den Namen auf dem Bild
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            #zu zeigen das bild aufm Bildschirm
            cv2.imshow('frame', frame)

        #für alle gefundenn Gesichte
        for (xA, yA, xB, yB) in face_locations:
            # zu zeigen das erneute Bild aufm Bildschirm
            cv2.imshow('Bildverarbeitung', frame)

            #zu finden wo die person ist
            xCenter = (left + right) / 2

            # zu erhalten die Breite vom Foto
            Width = frame.shape[1]
            Height = frame.shape[0]  # für die zukunftige Recherche. Für den 2 Servomotor

            #zu definiren die IP Adresse des EDGE-Geräts
            URL = "http://172.20.10.2:8000/"

            #wenm die Person von Links sich befindet
            if (xCenter < Width / 4):
                URL += "move_left"
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)

            # wenm die Person von Rechts sich befindet
            elif (xCenter > 3 * Width / 4):
                URL += "move_right"
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)
            # wenn der servomotor sich bewegen soll
            if 'move' in URL:
                r = requests.get(url=URL)
            break

        # wenn es erkannte Gisichte gibt, erneut sich das Bildschirm mit einem neuen  Foto
        if (len(face_locations) > 0):
            cv2.imshow("frame", frame)
            continue

        #Wenn keine gesichte erkannt sind aber jemand ist in der Nähe
        #zu verwenden HOG-Algorithmus
        boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8))

        #wenn jemand ist in der Sicht von der Kamera
        if len(boxes) > 0:
            personGefunden = True
        # wenn jemand nicht ist in der Sicht von der Kamera
        else:
            personGefunden = False

            #zu erhalten den Servomotorszustand
            URL = "http://172.20.10.2:8000/get_kamera_winkel"
            r = requests.get(url=URL)

            #wenn die Grenze erreicht ist, muss die einrichtung gewechselt werden
            if (int(r.text) == 12 or int(r.text) == 2):
                direction *= -1

            #anhängig von dem richtung ui zu definieren den richtigen REST-Service
            if (direction == 1):
                URL = "http://172.20.10.2:8000/move_right"
            else:
                URL = "http://172.20.10.2:8000/move_left"

            # zu schicken das request
            r = requests.get(url=URL)

            #abwarten bis zum Ende der Operation
            time.sleep(0.3)
            continue

        #jjemand ist in der Sicht der Kamera
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

        # für alle gefundenen Persone
        for (xA, yA, xB, yB) in boxes:
            # hinzuzufügen die rahen auf dem Foto
            cv2.rectangle(frame, (xA, yA), (xB, yB),
                          (0, 255, 0), 2)

            xCenter = (xB + xA) / 2

            Width = frame.shape[1]

            # zu definiern den EDGE-gerät URL
            URL = "http://172.20.10.2:8000/"

            # wenn die Person von Links sich befindet
            if (xCenter < Width / 4):
                # move_left
                URL += "move_left"
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)
            # wenn die Person von Rechts sich befindet
            elif (xCenter > 3 * Width / 4):
                # move_right
                URL += "move_right"
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)

            # zu zeigen das Foto aufm Bildschirm
            cv2.imshow('frame', frame)

            #wenn der Servomotor sich bewegen muss
            if 'move' in URL:
                r = requests.get(url=URL)
            break
        # wenn der Benutzer eine Taste drückt, muss die Program beendet werden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


# zu starten die Program
if __name__ == "__main__":
    main()
