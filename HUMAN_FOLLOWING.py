# from flask import Flask, Response, render_template_string
# import cv2
# import mediapipe as mp
# import threading

# # ----------------- Flask Setup -----------------
# app = Flask(__name__)

# # ----------------- Mediapipe Setup -----------------
# mp_pose = mp.solutions.pose
# pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
# mp_draw = mp.solutions.drawing_utils

# # ----------------- Camera Setup -----------------
# CAM_INDEX = 0
# FRAME_WIDTH, FRAME_HEIGHT = 320, 240  # lower resolution for RasPi

# cap = cv2.VideoCapture(CAM_INDEX)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# # ----------------- Threaded Frame Capture -----------------
# frame_lock = threading.Lock()
# latest_frame = None
# running = True

# def capture_frames():
#     global latest_frame
#     while running:
#         ret, frame = cap.read()
#         if not ret:
#             continue
#         with frame_lock:
#             latest_frame = frame.copy()

# threading.Thread(target=capture_frames, daemon=True).start()

# # ----------------- Helper Function -----------------
# def get_horizontal_position(x, width):
#     if x < width / 3:
#         return "Left"
#     elif x > 2 * width / 3:
#         return "Right"
#     else:
#         return "Center"

# # ----------------- Frame Generator for Flask -----------------
# def gen_frames():
#     global latest_frame
#     while True:
#         with frame_lock:
#             if latest_frame is None:
#                 continue
#             frame = latest_frame.copy()

#         img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = pose.process(img_rgb)

#         if results.pose_landmarks:
#             mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

#             h, w, _ = frame.shape
#             x_coords = [lm.x for lm in results.pose_landmarks.landmark]
#             y_coords = [lm.y for lm in results.pose_landmarks.landmark]

#             x_min, x_max = int(min(x_coords)*w), int(max(x_coords)*w)
#             y_min, y_max = int(min(y_coords)*h), int(max(y_coords)*h)

#             cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

#             center_x = (x_min + x_max) // 2
#             position = get_horizontal_position(center_x, w)

#             box_height = y_max - y_min
#             distance = round(1000 / box_height, 2)

#             cv2.putText(frame, f"Position: {position}", (10, 20),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
#             cv2.putText(frame, f"Distance: {distance}", (10, 40),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
#         else:
#             cv2.putText(frame, "No human detected", (10, 20),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame_bytes = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# # ----------------- Flask Routes -----------------
# HTML_TEMPLATE = """
# <html>
# <head>
# <title>RasPi Human Tracking</title>
# <style>
# body { text-align: center; background: #222; color: #eee; font-family: Arial; }
# img { border: 3px solid #555; margin-top: 20px; }
# </style>
# </head>
# <body>
# <h1>Raspberry Pi Human Tracking</h1>
# <img src="{{ url_for('video_feed') }}" width="640" height="480">
# </body>
# </html>
# """

# @app.route('/')
# def index():
#     return render_template_string(HTML_TEMPLATE)

# @app.route('/video_feed')
# def video_feed():
#     return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# # ----------------- Run Server -----------------
# if __name__ == '__main__':
#     try:
#         app.run(host='0.0.0.0', port=5000, debug=False)
#     finally:
#         running = False
#         cap.release()

from flask import Flask, Response, render_template_string
import cv2
import mediapipe as mp
import threading
from pyfirmata import Arduino, util
import time

# ----------------- Arduino Setup -----------------
board = Arduino('/dev/ttyUSB0')  # Change if needed
it = util.Iterator(board)
it.start()
time.sleep(1)  # Give Firmata some time

# L298N Pins
IN1 = board.get_pin('d:8:o')
IN2 = board.get_pin('d:9:o')
IN3 = board.get_pin('d:10:o')
IN4 = board.get_pin('d:11:o')

def stop():
    IN1.write(0)
    IN2.write(0)
    IN3.write(0)
    IN4.write(0)

def forward():
    IN1.write(1)
    IN2.write(0)
    IN3.write(1)
    IN4.write(0)

def backward():
    IN1.write(0)
    IN2.write(1)
    IN3.write(0)
    IN4.write(1)

def turn_left():
    IN1.write(0)
    IN2.write(1)
    IN3.write(1)
    IN4.write(0)

def turn_right():
    IN1.write(1)
    IN2.write(0)
    IN3.write(0)
    IN4.write(1)

# ----------------- Flask Setup -----------------
app = Flask(__name__)

# ----------------- Mediapipe Setup -----------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# ----------------- Camera Setup -----------------
CAM_INDEX = 0
FRAME_WIDTH, FRAME_HEIGHT = 320, 240

cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# ----------------- Threaded Frame Capture -----------------
frame_lock = threading.Lock()
latest_frame = None
running = True

def capture_frames():
    global latest_frame
    while running:
        ret, frame = cap.read()
        if not ret:
            continue
        with frame_lock:
            latest_frame = frame.copy()

threading.Thread(target=capture_frames, daemon=True).start()

# ----------------- Helper Function -----------------
def get_horizontal_position(x, width):
    if x < width / 3:
        return "Left"
    elif x > 2 * width / 3:
        return "Right"
    else:
        return "Center"

# ----------------- Frame Generator -----------------
def gen_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)

        h, w, _ = frame.shape
        position = "None"

        if results.pose_landmarks:
            mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            x_coords = [lm.x for lm in results.pose_landmarks.landmark]
            y_coords = [lm.y for lm in results.pose_landmarks.landmark]

            x_min, x_max = int(min(x_coords)*w), int(max(x_coords)*w)
            y_min, y_max = int(min(y_coords)*h), int(max(y_coords)*h)

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            center_x = (x_min + x_max) // 2
            position = get_horizontal_position(center_x, w)

            box_height = y_max - y_min
            distance = round(1000 / box_height, 2)

            cv2.putText(frame, f"Position: {position}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(frame, f"Distance: {distance}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        else:
            cv2.putText(frame, "No human detected", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # ---- Arduino Motor Control ----
        if position == "Left":
            turn_left()
        elif position == "Right":
            turn_right()
        elif position == "Center":
            forward()
        else:
            stop()

        # ----------------- Yield Frame -----------------
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ----------------- Flask Routes -----------------
HTML_TEMPLATE = """
<html>
<head>
<title>RasPi Human Tracking</title>
<style>
body { text-align: center; background: #222; color: #eee; font-family: Arial; }
img { border: 3px solid #555; margin-top: 20px; }
</style>
</head>
<body>
<h1>Raspberry Pi Human Tracking</h1>
<img src="{{ url_for('video_feed') }}" width="640" height="480">
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ----------------- Run Server -----------------
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        running = False
        stop()
        cap.release()
