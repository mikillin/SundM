from flask import Flask, Response, json
import numpy as np
import cv2

app = Flask(__name__)

global_frame = None

def generate_frames():
    # OpenCV Video Capture
    cap = cv2.VideoCapture(0)  # Change the parameter to the index of your camera

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


@app.route('/image')
def imageCurrent():

    return global_frame


@app.route('/json')
def jsonExample():
    data = {
        "name": "John",
        "age": 30,
        "city": "New York"
    }
    return json.dumps(data)

@app.route('/')
def index():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)  # Run the server on port 8000
