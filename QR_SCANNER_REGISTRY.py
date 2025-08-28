from flask import Flask, render_template_string, Response
import cv2
from pyzbar.pyzbar import decode
import threading
import time

# ----------------- Flask Setup -----------------
app = Flask(__name__)

# ----------------- Cart -----------------
cart = {}
total = 0
prev_y = None

# ----------------- Camera Setup -----------------
camera_index = 0  # Change if necessary
cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)

frame_lock = threading.Lock()
latest_frame = None

# ----------------- HTML Template -----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Smart Trolley</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }
        h1 { color: #333; }
        #cart { margin-top: 20px; }
        table { margin: auto; border-collapse: collapse; width: 50%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #4CAF50; color: white; }
        td { text-align: center; }
    </style>
</head>
<body>
    <h1>📷 Smart Trolley QR Scanner</h1>
    <img src="{{ url_for('video_feed') }}" width="320" height="240">
    <div id="cart">
        <h2>🧾 Cart Registry</h2>
        <table>
            <tr>
                <th>Product</th>
                <th>Quantity</th>
            </tr>
            {% for item, qty in cart.items() %}
            <tr>
                <td>{{ item }}</td>
                <td>{{ qty }}</td>
            </tr>
            {% endfor %}
            <tr>
                <th>Total</th>
                <th>Rs.{{ total }}</th>
            </tr>
        </table>
    </div>
</body>
</html>
"""

# ----------------- Threaded Frame Capture -----------------
def capture_frames():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        with frame_lock:
            latest_frame = frame.copy()
        time.sleep(0.01)  # small delay to avoid CPU overload

threading.Thread(target=capture_frames, daemon=True).start()

# ----------------- Frame Generator -----------------
def gen_frames():
    global prev_y, cart, total
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            try:
                product, price = qr_data.split(",")
                product = product.strip()
                price = float(price.strip())
            except:
                continue

            # QR center
            x, y, w, h = obj.rect
            center_y = y + h // 2

            if prev_y is not None:
                if center_y > prev_y + 15:  # moved down → add
                    cart[product] = cart.get(product, 0) + 1
                    total += price
                elif center_y < prev_y - 15:  # moved up → remove
                    if product in cart and cart[product] > 0:
                        cart[product] -= 1
                        total -= price
                        if cart[product] == 0:
                            del cart[product]
            prev_y = center_y

            # Draw rectangle + text
            pts = obj.polygon
            for j in range(len(pts)):
                cv2.line(frame, pts[j], pts[(j + 1) % len(pts)], (0, 255, 0), 2)
            cv2.putText(frame, f"{product} Rs.{price}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(frame, f"Total: Rs.{total}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Encode JPEG with lower quality for faster streaming
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)  # ~30 FPS cap

# ----------------- Flask Routes -----------------
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, cart=cart, total=total)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ----------------- Run Flask -----------------
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        cap.release()
