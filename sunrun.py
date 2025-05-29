import time
import board
from board import SCL, SDA
import adafruit_ltr390
import adafruit_l3gd20
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import random

import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold  # Import only necessary types
from google.generativeai import types
from dotenv import load_dotenv, find_dotenv
import streamlit as st
import faiss
import numpy as np
from gtts import gTTS

key = os.getenv("KEY")
genai.configure(api_key="YOUR API KEY HERE")
model = genai.GenerativeModel("embedding-ada") 

model = genai.GenerativeModel("gemini-2.0-flash")  # or whatever conversational model you prefer

def whimsical_plant_speak(prompt_hint):
    response = model.generate_content(
        f"You are a tiny whimsical plant who is narrating what you are doing. Speak in a cute, nature-inspired way. Say something when you are {prompt_hint}. Keep it to a single sentence."
    )
    message = response.text
    print(message)
    #speak_text(message)
    #return message

'''
def speak_text(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    filename = f"plant_say_{random.randint(0, 1_000_000)}.mp3"
    tts.save(filename)
    os.system(f"mpg123 {filename}")  # macOS/Linux: use mpg123, Windows: use playsound
    os.remove(filename)'''


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
        print(whimsical_plant_speak("starting to spin joyfully in the sun"))
        spin_servos(SERVO_SPEED)
        time.sleep(SPIN_DURATION)
        stop_servos()

        print(whimsical_plant_speak("pausing to measure the sunshine with my leafy sensors"))
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

        print(whimsical_plant_speak("finding the sunniest direction to grow toward"))

        # Find angle with highest lux
        if lux_angle_map:
            best_angle, max_lux = max(lux_angle_map, key=lambda x: x[1])
            print(whimsical_plant_speak(f"I'm growing toward the sun at {best_angle:.2f}°"))
        else:
            print(">> No lux data recorded. Skipping rotation.")
            time.sleep(SLEEP_BETWEEN_CYCLES)
            continue

        # === ROTATE TO TARGET ANGLE ===
        print(whimsical_plant_speak("turning myself slowly toward the warmest light"))
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
        print(whimsical_plant_speak("moving forward with green ambition"))

        # === MOVE FORWARD ===
        print(whimsical_plant_speak("moving forward with green ambition"))
        move_forward()
        time.sleep(1)
        stop_servos()

        # Wait before next cycle
        print(whimsical_plant_speak("resting before I twirl again"))
        time.sleep(SLEEP_BETWEEN_CYCLES)

except KeyboardInterrupt:
    servo_left.angle = None
    servo_right.angle = None
    print("Stopped by User")
