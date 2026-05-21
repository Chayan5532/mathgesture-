from cvzone.HandTrackingModule import HandDetector
import cv2
import cvzone
import numpy as np
import os
from google import genai
from PIL import Image
import streamlit as st
import time  # FIXED: for rate limiting

st.set_page_config(layout="wide")
st.image('mathGestures.png')

col1,col2 = st.columns([3,2])
with col1:
    run = st.checkbox("Run",value=True)
    FRAME_WINDOW = st.image([])

with col2:
    st.title("Answer")
    output_text_area = st.subheader("")

# FIXED: removed extra space in API key
client = genai.Client(api_key="AIzaSyDBOA7LTQXAGQsEuCSOKKmB2Q3YKKULLTs")
model="gemini-2.0-flash"

# Initialize the webcam to capture video
cap = cv2.VideoCapture(0)
cap.set(propId=3,value=1280)
cap.set(propId=4,value=720)

# Initialize the HandDetector class
detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=1, detectionCon=0.7, minTrackCon=0.5)

def getHandInfo(img):
    hands, img = detector.findHands(img, draw=False, flipType=True)

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        fingers = detector.fingersUp(hand)
        print(fingers)
        return fingers, lmList
    else:
        return None

# FIXED: added img parameter
def draw(info,prev_pos,canvas,img):
    fingers, lmList = info
    current_pos = None

    if fingers == [0,1,0,0,0]:
        current_pos = lmList[8][0:2]
        if prev_pos is None:
            prev_pos = current_pos
        # FIXED: thicker drawing
        cv2.line(canvas,current_pos,prev_pos,(255,0,255),15)

    elif fingers == [1,1,1,1,1]:
        canvas = np.zeros_like(img)

    return current_pos,canvas

# FIXED: rate limit added + better handling
last_call = 0

def sendToAI(canvas,fingers):
    global last_call

    if fingers == [1,1,0,0,1]:
        current_time = time.time()

        # FIXED: call only every 5 seconds
        if current_time - last_call > 5:
            last_call = current_time

            pil_image = Image.fromarray(canvas)
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=["Solve this math problem", pil_image]
                )
                return response.text
            except Exception as e:
                return str(e)

    return None

prev_pos = None
canvas = None
image_combined = None
output_text = ""

while run:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    if canvas is None:
        canvas = np.zeros_like(img)

    info = getHandInfo(img)

    if info:
        fingers, lmList = info
        prev_pos,canvas = draw(info, prev_pos, canvas, img)

        # FIXED: prevent overwrite issue
        result = sendToAI(canvas,fingers)
        if result:
            output_text = result

    image_combined = cv2.addWeighted(img,0.7,canvas,0.3,0)
    FRAME_WINDOW.image(image_combined,channels="BGR")

    if output_text:
        output_text_area.text(output_text)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# streamlit run "C:\ML project\main.py"
