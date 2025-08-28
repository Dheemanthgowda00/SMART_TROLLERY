from flask import Flask, Response, render_template_string
import cv2
import threading
import time

app = Flask(__name__)

# ----------------- CAMERA SETUP -----------------
camera_index = 0
cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)

# Reduce resolution for faster streaming
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    raise RuntimeError(f"Cannot open camera at index {camera_index}")

frame_lock = threading.Lock()
latest_frame = None

def capture_frames():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        # Optional: convert to grayscale to reduce size
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        with frame_lock:
            latest_frame = frame.copy()
        time.sleep(0.01)  # give CPU breathing room

threading.Thread(target=capture_frames, daemon=True).start()

# ----------------- FLASK ROUTES -----------------
@app.route('/')
def index():
    html = """
    <html>
    <head>
        <title>Pi Camera Stream</title>
        <style>
            body { text-align: center; background-color: #222; color: #eee; }
            h1 { margin-top: 20px; }
            img { border: 5px solid #555; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Pi Camera Live Stream</h1>
        <img src="{{ url_for('video_feed') }}" width="320" height="240">
    </body>
    </html>
    """
    return render_template_string(html)

def generate_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.01)
            continue
        with frame_lock:
            # Resize to reduce JPEG size
            frame = cv2.resize(latest_frame, (320, 240))
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)  # throttle to ~30 FPS max

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        cap.release()
