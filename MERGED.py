import cv2
from pyzbar.pyzbar import decode
from pyfirmata import Arduino, util
import time
import json
import threading
import sys

# ----------------- Arduino IR -----------------
board = Arduino('/dev/ttyUSB0')  # Change to your Arduino port
it = util.Iterator(board)
it.start()

ir1 = board.get_pin('d:2:i')  # Add zone sensor
ir2 = board.get_pin('d:3:i')  # Remove zone sensor
time.sleep(1)  # stabilize

# ----------------- CART -----------------
cart = {}
total = 0.0
last_product = None
last_price = 0.0
last_qr_raw = None
lock = threading.Lock()

# ----------------- JSON Save -----------------
def save_cart():
    with lock:
        data = {
            "cart": cart,
            "total": total
        }
        with open("cart.json", "w") as f:
            json.dump(data, f, indent=4)

# ----------------- QR Reader -----------------
def qr_scanner():
    global last_product, last_price, last_qr_raw
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            last_qr_raw = qr_data  # store raw QR
            try:
                product, price_val = qr_data.split(",")
                product_name = product.strip()
                price = float(price_val.strip())

                last_product = product_name
                last_price = price

                print(f"📷 QR Detected: RAW='{qr_data}' | Parsed={product_name} Rs.{price}")
            except Exception as e:
                print(f"⚠️ QR Detected but parsing failed: RAW='{qr_data}' | Error: {e}")
                continue

        time.sleep(0.1)

# ----------------- IR Logic -----------------
def ir_monitor():
    global last_product, last_price, last_qr_raw, total
    while True:
        s1 = ir1.read()
        s2 = ir2.read()

        if s1 is False and last_product:  # Add product
            cart[last_product] = cart.get(last_product, 0) + 1
            total += last_price
            print(f"➕ Added {last_product} | Rs.{last_price} | Total: Rs.{total} | QR='{last_qr_raw}'")
            save_cart()
            last_product = None
            last_qr_raw = None
            time.sleep(0.3)  # debounce

        if s2 is False and last_product:  # Remove product
            if cart.get(last_product, 0) > 0:
                cart[last_product] -= 1
                total -= last_price
                print(f"➖ Removed {last_product} | Rs.{last_price} | Total: Rs.{total} | QR='{last_qr_raw}'")
                if cart[last_product] == 0:
                    del cart[last_product]
                save_cart()
            last_product = None
            last_qr_raw = None
            time.sleep(0.3)

        time.sleep(0.05)

# ----------------- MAIN -----------------
if __name__ == "__main__":
    print("🛒 Smart Trolley Console Mode Started")
    print("👉 Scanning QR codes, using IR sensors, updating cart.json")

    try:
        threading.Thread(target=qr_scanner, daemon=True).start()
        ir_monitor()  # runs forever
    except KeyboardInterrupt:
        print("\n❌ Exiting...")
        board.exit()
        sys.exit(0)
