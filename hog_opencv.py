# das Import der erforderlichen Bibliotheken
import urllib.request
import urllib.request

import cv2
import face_recognition
import numpy as np
import requests
import time


#Name des Fenster vom Videostream
NAME_DES_FENSTER = "Signalverarbeitung und Mustererkennung"

# Lokale IP-Adresse des EDGE-Geräts
URL = 'http://192.168.178.130:8000'


# Statische IP-Adresse des EDGE-Geräts, wenn Gerät durch den Internet zugegriffen werden muss
# url = 'http://78.94.176.119:8000/image_shot'

# die Funktion fordert ein Bild vom EDGE-Gerät an
def getRemoteImage():
    # REST-URL von der Bildquelle
    url = URL + '/image_shot'

    #  Formatieren des erhalten Bilds vom Response
    with urllib.request.urlopen(url) as resp:
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    return image


# Die Hauptmethode mit der Hauptlogik
def main():
    # Initialisierung der Variable "bewegungIdentifitiert"
    bewegungIdentifitiert = False

    # solange kein Besucher identifiziert ist, müssen keine weitere Schritte unternommen werden
    while not bewegungIdentifitiert:

        url_REST = URL + "/isvisited"
        # Auslesen des Statuses von dem Bewegungssensor
        r = requests.get(url=url_REST)

        if (int(r.text) == 1):
            bewegungIdentifitiert = True
            break

        # Zeitraum zwischen den Anfragen
        time.sleep(2)

    # Foto des Besitzers muss definiert werden
    owner_image = face_recognition.load_image_file("Besitzer.png")

    # Merkmale des Fotos des Besitzers zu dekodieren
    owner_face_encoding = face_recognition.face_encodings(owner_image)[0]

    # Wenn viele Besitzer angegeben werden müssen, können alle Fotos hinzugefügt werden
    known_face_encodings = [
        owner_face_encoding
    ]
    # Den entsprechenden Namen müssen  definiert werden
    known_face_names = [
        "Besitzer"
    ]

    # Initialisierung den HOG-Deskriptoren
    hog = cv2.HOGDescriptor()

    # Initialization den SVM-Detektoren laut den HOG Deskriptoren
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # Start eines neuen Threads, um viele Clients zusammenarbeiten zu können
    cv2.startWindowThread()

    # Initialization des Servomotors
    url_REST = URL + '/motor_init'

    # Ausführung des REST-Befehls
    requests.get(url=url_REST)

    # Initialisierung der Richtung der Bewegung der Kamera.
    direction = 1

    # Solange jemand in der Nähe sich befindet, muss die Kamera die identifizierte Persone beobachten
    while (bewegungIdentifitiert):

        # abhängig vom Servomotor ist es notwendig abzuwarten, bis zum Moment,
        # wann der Motor die Bewegung durchgeführt haben wird

        # 0.3 Sekunden reichen, um der Servomotor auf 18 Grade sich drehen zu kännen.
        # Der Wert ist abhängig vom Typ des Servomotors
        time.sleep(0.5)

        # Foto von der Kamera  des EDGE-Geräts zu erhalten
        frame = getRemoteImage()

        #  Foto auf die Speicherkarte für spätere Analyse zu speichern
        cv2.imwrite("image.jpg", frame)

        # Pause, um die Raspberry Pi Platte den Befehl bis zum Ende ausführen zu können
        time.sleep(0.5)

        # Foto aufm Bildschirm zu zeigen
        cv2.imshow(NAME_DES_FENSTER, frame)

        # Gesichtserkennung
        # Foto laut des passenden Formats muss  formatiert werden
        rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])

        # Suche nach der Positionen den Gesichter
        face_locations = face_recognition.face_locations(rgb_frame)

        # Erkannte Gesichter werden kodiert
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Jedes Gesicht wird bearbeitet
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            # Initialisation des Namens der erkennten Person
            name = "Unbekannt"

            # Bekannte Gesichter werden gesucht
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            # Gesicht, dass ähnlich ambestens dem bekannten Gesciht ist, wird gefunden
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            # Eine Person ist in der Nähe und ist identifiziert
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                # Das Foto von der Person ist als "Besitzer" gegeben
                if name == "Besitzer":
                    # in diesem Fall muss die grüne LED angeschaltet werden
                    url_REST = URL + "/green_led"  # start streaming
                    requests.get(url=url_REST)
            else:
                # ansonsten muss die rote LED angeschaltet werden
                url_REST = URL + "/red_led"  # start streaming
                requests.get(url=url_REST)

            # Mit der Rahmen müssen alle Gesichter auf dem Bild markiert werden
            cv2.rectangle(frame, (left - 50, top - 50), (right + 50, bottom + 50), (0, 0, 255), 2)

            # Neben der Rahmen auf dem Bild muss der Name der Person angeschrieben werden
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            # Für den Text muss der Schrift definiert werden
            font = cv2.FONT_HERSHEY_DUPLEX
            # Name muss auf dem Bild  hinzugefügt werden
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Das Bild muss auf dem Bildschirm angezeigt werden
            cv2.imshow('Signalverarbeitung und Mustererkennung', frame)

        # Wenn Person nicht aufm Foto zentriert sein, muss Kamera sich drehen
        # alle Gesichter müssen verarbeitet werden
        for (xA, yA, xB, yB) in face_locations:
            # das erneute Bild muss aufm Bildschirm angezeigt werden
            cv2.imshow('Signalverarbeitung und Mustererkennung', frame)

            # Kalkulation des Zentrums, wo die erkannte Person sich befindet
            xCenter = (left + right) / 2

            # die Breite vom Foto muss kalkuliert werden
            Width = frame.shape[1]

            # wenn die Person von Links sich befindet
            if (xCenter < Width / 4):
                url_REST = URL + "move_left"

                #Person muss in diesem Fall mit roten Rahmen markiert werden
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)

            # wenn die Person von Rechts sich befindet
            elif (xCenter > 3 * Width / 4):
                url_REST = URL + "move_right"
                # Person muss in diesem Fall mit roten Rahmen markiert werden
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)
            # wenn der Servomotor sich bewegen soll, wird ein Request dem EDGE-Gerät abgeschickt werden
            if 'move' in url_REST:
                requests.get(url=url_REST)
            break

        # wenn es erkannte Gesichter gibt, erneuert sich das Bildschirm mit einem neuen Foto
        cv2.imshow(NAME_DES_FENSTER, frame)
        if (len(face_locations) > 0):
            continue

        # Wenn keine Gesichter erkannt sind aber jemand  in der Nähe ist
        # wird der HOG-Algorithmus verwendet
        boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8))

        # wenn niemand ist mit der Kamera identifiziert
        if len(boxes) == 0:

            # Servomotorszustand muss bekannt sein
            url_REST = URL + "/get_camera_angle"
            r = requests.get(url=url_REST)

            # wenn die Grenze des Servomotors erreicht ist, muss die Richtung der Drehung gewechselt werden
            if (int(r.text) == 12 or int(r.text) == 2):
                direction *= -1

            # abhängig von der ehemaligen Richtung der Bewegung der Kamera,
            # muss das entsprechende Request zu EDGE-Gerät abgeschickt werden
            if (direction == 1):
                url_REST = URL + "/move_right"
            else:
                url_REST = URL + "/move_left"

            # Befehl zu schicken
            requests.get(url=url_REST)

            # Bis zum Ende der Operation abzuwarten
            time.sleep(0.3)
            continue

        # zumindest ein Besucher ist mit der Kamera identifiziert
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

        # alle Persone aufm Foto müssen verarbeitet werden
        for (xA, yA, xB, yB) in boxes:
            # Rahmen müssen auf dem Foto hinzugefügt werden, um Person zu markieren
            cv2.rectangle(frame, (xA, yA), (xB, yB),
                          (0, 255, 0), 2)

            #das Zentrum von der Person aufm Bild ist notwendig zu kalkulieren
            xCenter = (xB + xA) / 2

            #Die Breite des Bildes muss kalkuliert werden, um zu definieren, wo  die Person aufm Foto sich befindet.
            Width = frame.shape[1]

            # wenn die Person von Links sich befindet, muss die Kamera nach rechts sich drehen
            if (xCenter < Width / 4):
                url_REST = URL + "/move_left"
                #Person muss in diesem Fall mit roten Rahmen markiert werden
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)
            # wenn die Person von Rechts sich befindet, muss die Kamera nach links sich drehen
            elif (xCenter > 3 * Width / 4):
                url_REST = URL + "/move_right"
                #Person muss in diesem Fall mit roten Rahmen markiert werden
                cv2.rectangle(frame, (xA, yA), (xB, yB),
                              (0, 0, 255), 2)

            # das erneute Bild muss aufm Bildschirm angezeigt werden
            cv2.imshow(NAME_DES_FENSTER, frame)

            # wenn der Servomotor sich bewegen muss, wird das Request abgeschickt werden
            if 'move' in url_REST:
                requests.get(url=url_REST)
            break

        # wenn der Benutzer eine Taste drückt, muss die Program beendet werden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


# Funktion startet den Algorithmen
if __name__ == "__main__":
    main()
