from pyfirmata import Arduino, util
import time

# ----------------- CONNECT TO ARDUINO -----------------
# Update to your RasPi Arduino port
board = Arduino('/dev/ttyUSB0')  # Usually /dev/ttyACM0 or /dev/ttyUSB0

# Start iterator to prevent buffer overflow
it = util.Iterator(board)
it.start()

# ----------------- IR PINS -----------------
ir1 = board.get_pin('d:2:i')  # digital pin 2, input
ir2 = board.get_pin('d:3:i')  # digital pin 3, input

# ----------------- COUNTER -----------------
count = 0
print("Smart Entry/Exit Counter Ready...")

# Give pins a moment to initialize
time.sleep(1)

# ----------------- MAIN LOOP -----------------
try:
    while True:
        s1 = ir1.read()
        s2 = ir2.read()

        # Skip iteration if readings not ready
        if s1 is None or s2 is None:
            time.sleep(0.01)
            continue

        # ----------------- ENTRY LOGIC -----------------
        if s1 == 0:  # LOW = obstacle
            time.sleep(0.05)
            if ir2.read() == 0:
                count += 1
                print(f"Entry detected → Count: {count}")
                # Wait until both sensors are clear
                while ir1.read() == 0 and ir2.read() == 0:
                    time.sleep(0.01)

        # ----------------- EXIT LOGIC -----------------
        if s2 == 0:
            time.sleep(0.05)
            if ir1.read() == 0:
                count -= 1
                if count < 0:
                    count = 0
                print(f"Exit detected → Count: {count}")
                # Wait until both sensors are clear
                while ir1.read() == 0 and ir2.read() == 0:
                    time.sleep(0.01)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting program...")
    board.exit()
