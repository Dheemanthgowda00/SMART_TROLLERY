# from flask import Flask, render_template, jsonify, request
# from pyfirmata import Arduino, util
# import cv2
# import time
# import mediapipe as mp
# from pyzbar.pyzbar import decode
# from threading import Thread
# import json
# import os

# # ----------------- ARDUINO IR SETUP -----------------
# board = Arduino('/dev/ttyUSB0')  # change for Pi
# it = util.Iterator(board)
# it.start()
# ir1 = board.get_pin('d:2:i')
# ir2 = board.get_pin('d:3:i')
# time.sleep(1)

# # ----------------- SMART TROLLEY SETUP -----------------
# CART_FILE = "cart.json"
# cart = {}
# total = 0
# last_product = None
# last_price = 0

# # Load cart from file if exists
# if os.path.exists(CART_FILE):
#     try:
#         with open(CART_FILE, "r") as f:
#             data = json.load(f)
#             cart = data.get("cart", {})
#             total = data.get("total", 0)
#     except:
#         cart = {}
#         total = 0

# def save_cart():
#     with open(CART_FILE, "w") as f:
#         json.dump({"cart": cart, "total": total}, f, indent=2)

# # ----------------- HUMAN FOLLOWING SETUP -----------------
# mp_pose = mp.solutions.pose
# pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# def get_horizontal_position(x, width):
#     if x < width/3: return "Left"
#     elif x > 2*width/3: return "Right"
#     else: return "Center"

# # ----------------- GLOBAL MODE -----------------
# mode = 's'  # default Smart Trolley

# # ----------------- FLASK SETUP -----------------
# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/status')
# def status():
#     return jsonify({
#         'mode': 'Smart Trolley' if mode == 's' else 'Human Following',
#         'cart': cart,
#         'total': total
#     })

# @app.route('/toggle', methods=['POST'])
# def toggle_mode():
#     global mode
#     mode = 'h' if mode == 's' else 's'
#     print(f"🔄 Switched to {'Human Following' if mode=='h' else 'Smart Trolley'} Mode")
#     return jsonify({'mode': mode})

# # ----------------- SMART TROLLEY FUNCTION -----------------
# def smart_trolley_mode(frame):
#     global last_product, last_price, cart, total
#     decoded_objects = decode(frame)
#     for obj in decoded_objects:
#         qr_data = obj.data.decode("utf-8")
#         try:
#             product, price_val = qr_data.split(",")
#             last_product = product.strip()
#             last_price = float(price_val.strip())
#         except:
#             continue

#     s1 = ir1.read()
#     s2 = ir2.read()
#     if s1 == 0 and last_product:
#         cart[last_product] = cart.get(last_product, 0) + 1
#         total += last_price
#         save_cart()  # Save whenever cart changes
#         print(f"➕ Added {last_product} | Rs.{last_price} | Total: Rs.{total}")
#         time.sleep(0.5)
#     if s2 == 0 and last_product:
#         if last_product in cart and cart[last_product] > 0:
#             cart[last_product] -= 1
#             total -= last_price
#             if cart[last_product] == 0:
#                 del cart[last_product]
#             save_cart()  # Save whenever cart changes
#             print(f"➖ Removed {last_product} | Rs.{last_price} | Total: Rs.{total}")
#         time.sleep(0.5)

# # ----------------- HUMAN FOLLOWING FUNCTION -----------------
# def human_following_mode(frame):
#     img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = pose.process(img_rgb)
#     if results.pose_landmarks:
#         h, w, c = frame.shape
#         x_coords = [lm.x for lm in results.pose_landmarks.landmark]
#         y_coords = [lm.y for lm in results.pose_landmarks.landmark]
#         x_min = int(min(x_coords) * w)
#         x_max = int(max(x_coords) * w)
#         y_min = int(min(y_coords) * h)
#         y_max = int(max(y_coords) * h)
#         center_x = (x_min + x_max) // 2
#         position = get_horizontal_position(center_x, w)
#         box_height = y_max - y_min
#         distance = round(1000 / box_height, 2)
#         print(f"👤 Human Position: {position} | Distance: {distance} a.u.")

# # ----------------- CAMERA LOOP -----------------
# def camera_loop():
#     cap = cv2.VideoCapture(0)
#     print("🚀 Camera loop running")
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             continue
#         if mode == 's':
#             smart_trolley_mode(frame)
#         else:
#             human_following_mode(frame)

# # ----------------- MAIN -----------------
# if __name__ == "__main__":
#     t = Thread(target=camera_loop, daemon=True)
#     t.start()
#     app.run(host='0.0.0.0', port=5000)

from flask import Flask, render_template, jsonify, request
from pyfirmata import Arduino, util
import cv2
import time
import mediapipe as mp
from pyzbar.pyzbar import decode
from threading import Thread
import json
import os

# ----------------- ARDUINO SETUP -----------------
board = Arduino('/dev/ttyUSB0')  # change for Pi
it = util.Iterator(board)
it.start()
time.sleep(1)

# IR Sensors
ir1 = board.get_pin('d:2:i')
ir2 = board.get_pin('d:3:i')

# L298N Motor Pins
IN1 = board.get_pin('d:8:o')
IN2 = board.get_pin('d:9:o')
IN3 = board.get_pin('d:10:o')
IN4 = board.get_pin('d:11:o')

# Motor control functions
def stop():
    IN1.write(0); IN2.write(0)
    IN3.write(0); IN4.write(0)

def forward():
    IN1.write(1); IN2.write(0)
    IN3.write(1); IN4.write(0)

def backward():
    IN1.write(0); IN2.write(1)
    IN3.write(0); IN4.write(1)

def turn_left():
    IN1.write(0); IN2.write(1)
    IN3.write(1); IN4.write(0)

def turn_right():
    IN1.write(1); IN2.write(0)
    IN3.write(0); IN4.write(1)

# ----------------- SMART TROLLEY SETUP -----------------
CART_FILE = "cart.json"
cart = {}
total = 0
last_product = None
last_price = 0

# Load existing cart
if os.path.exists(CART_FILE):
    try:
        with open(CART_FILE, "r") as f:
            data = json.load(f)
            cart = data.get("cart", {})
            total = data.get("total", 0)
    except:
        cart = {}
        total = 0

def save_cart():
    with open(CART_FILE, "w") as f:
        json.dump({"cart": cart, "total": total}, f, indent=2)

# ----------------- HUMAN FOLLOWING SETUP -----------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def get_horizontal_position(x, width):
    if x < width/3: return "Left"
    elif x > 2*width/3: return "Right"
    else: return "Center"

# ----------------- GLOBAL MODE -----------------
mode = 's'  # default Smart Trolley

# ----------------- FLASK SETUP -----------------
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        'mode': 'Smart Trolley' if mode == 's' else 'Human Following',
        'cart': cart,
        'total': total
    })

@app.route('/toggle', methods=['POST'])
def toggle_mode():
    global mode
    mode = 'h' if mode == 's' else 's'
    print(f"🔄 Switched to {'Human Following' if mode=='h' else 'Smart Trolley'} Mode")
    stop()  # Stop motors when mode switches
    return jsonify({'mode': mode})

# ----------------- SMART TROLLEY FUNCTION -----------------
def smart_trolley_mode(frame):
    global last_product, last_price, cart, total
    decoded_objects = decode(frame)
    for obj in decoded_objects:
        qr_data = obj.data.decode("utf-8")
        try:
            product, price_val = qr_data.split(",")
            last_product = product.strip()
            last_price = float(price_val.strip())
        except:
            continue

    s1 = ir1.read()
    s2 = ir2.read()
    if s1 == 0 and last_product:
        cart[last_product] = cart.get(last_product, 0) + 1
        total += last_price
        save_cart()
        print(f"➕ Added {last_product} | Rs.{last_price} | Total: Rs.{total}")
        time.sleep(0.5)
    if s2 == 0 and last_product:
        if last_product in cart and cart[last_product] > 0:
            cart[last_product] -= 1
            total -= last_price
            if cart[last_product] == 0:
                del cart[last_product]
            save_cart()
            print(f"➖ Removed {last_product} | Rs.{last_price} | Total: Rs.{total}")
        time.sleep(0.5)

# ----------------- HUMAN FOLLOWING FUNCTION -----------------
def human_following_mode(frame):
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)
    if results.pose_landmarks:
        h, w, c = frame.shape
        x_coords = [lm.x for lm in results.pose_landmarks.landmark]
        y_coords = [lm.y for lm in results.pose_landmarks.landmark]
        x_min = int(min(x_coords) * w)
        x_max = int(max(x_coords) * w)
        y_min = int(min(y_coords) * h)
        y_max = int(max(y_coords) * h)
        center_x = (x_min + x_max) // 2
        position = get_horizontal_position(center_x, w)
        box_height = y_max - y_min
        distance = round(1000 / box_height, 2)
        print(f"👤 Human Position: {position} | Distance: {distance} a.u.")

        # --- MOTOR CONTROL BASED ON POSITION ---
        if position == "Left":
            turn_left()
        elif position == "Right":
            turn_right()
        elif position == "Center":
            forward()
        else:
            stop()
    else:
        stop()  # Stop if no human detected

# ----------------- CAMERA LOOP -----------------
def camera_loop():
    cap = cv2.VideoCapture(0)
    print("🚀 Camera loop running")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        if mode == 's':
            smart_trolley_mode(frame)
            stop()  # Ensure motors stay stopped in Smart Trolley mode
        else:
            human_following_mode(frame)

# ----------------- MAIN -----------------
if __name__ == "__main__":
    t = Thread(target=camera_loop, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)
