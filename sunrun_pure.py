import time
import board
from board import SCL, SDA
import adafruit_ltr390
import adafruit_l3gd20
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import random

##I2C Setup
I2C = board.I2C() # uses board.SCL and board.SDA

## Gyro Setup
gyro = adafruit_l3gd20.L3GD20_I2C(I2C)
rate=adafruit_l3gd20.L3DS20_RATE_200HZ

## Servo Setup
pca = PCA9685(I2C)
pca.frequency = 50
servo_left = servo.Servo(pca.channels[0])  # Channel 1
servo_right = servo.Servo(pca.channels[3])  # Channel 4

## UV Setup
ltr = adafruit_ltr390.LTR390(I2C)

# === CONSTANTS ===
SPIN_DURATION = 3           # seconds
SCAN_DURATION = 5           # seconds
SERVO_SPEED = 90            # degrees, adjust as needed
SLEEP_BETWEEN_CYCLES = 5    # seconds

# === FUNCTIONS ===

def spin_servos(speed):
    servo_left.angle = safe_angle(SERVO_SPEED)
    servo_right.angle = safe_angle(SERVO_SPEED)

def stop_servos():
    servo_left.angle = 90
    servo_right.angle = 90

def move_forward():
    servo_left.angle = safe_angle(SERVO_SPEED)
    servo_right.angle = safe_angle(-SERVO_SPEED)

def safe_angle(offset):
    return max(0, min(180, 90 + offset))

# === MAIN LOOP ===
try:
    while True:
        print("Starting my whimiscal spin.")
        spin_servos(SERVO_SPEED)
        time.sleep(SPIN_DURATION)
        stop_servos()

        print("Pausing to measure the sunshine with my leafy sensors.")
        start_time = time.monotonic()
        current_angle = 0.0
        last_time = time.monotonic()
        lux_angle_map = []

        while (time.monotonic() - start_time) < SPIN_DURATION:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            # Get angular velocity (rad/s), convert to deg/s
            angular_velocity_z = gyro.gyro[2] * (180 / 3.141592)
            d_angle = angular_velocity_z * dt
            current_angle += d_angle

            # Normalize angle between 0-360
            normalized_angle = current_angle % 360

            # Get lux
            try:
                lux = ltr.light  # or ltr.uvs if you prefer UV
                lux_angle_map.append((normalized_angle, lux))
            except:
                pass  # skip any read errors

            time.sleep(0.01)  # sample at ~100Hz

        print("Finding the sunniest direction to grow toward.")

        # Find angle with highest lux
        if lux_angle_map:
            best_angle, max_lux = max(lux_angle_map, key=lambda x: x[1])
            print("I'm growing toward the sun at {best_angle:.2f}°")
        else:
            print(">> No lux data recorded. Skipping rotation.")
            time.sleep(SLEEP_BETWEEN_CYCLES)
            continue

        # === ROTATE TO TARGET ANGLE ===
        print("I'm turning myself slowly toward the warmest light")
        current_angle = 0.0
        last_time = time.monotonic()
        spin_servos(SERVO_SPEED)

        while abs(current_angle % 360 - best_angle) > 5:
            now = time.monotonic()
            dt = now - last_time
            last_time = now
            angular_velocity_z = gyro.gyro[2] * (180 / 3.141592)
            d_angle = angular_velocity_z * dt
            current_angle += d_angle

            time.sleep(0.01)

        stop_servos()
        print("Moving forward with green ambition")

        # === MOVE FORWARD ===
        print("Moving forward with green ambition")
        move_forward()
        time.sleep(1)
        stop_servos()

        # Wait before next cycle
        print("Resting before I twirl again")
        time.sleep(SLEEP_BETWEEN_CYCLES)

except KeyboardInterrupt:
    servo_left.angle = None
    servo_right.angle = None
    print("Giving my leaves a rest.")