import cv2
import time
from frankie_stt_tts import speak, listen_once, get_reply


# set up webcam 

cap = cv2.VideoCapture(0)

# MOG2 seperates moving people from background
fgbg = cv2.createBackgroundSubtractorMOG2(
    history=300,
    varThreshold=50,
    detectShadows=False
    
)
# store previous size/position of movement
prev_area = None
prev_cx = None
approach_count = 0
DECAY = 1

STATE = "IDLE"   # IDLE → ENGAGED

print("Frankie V2 Running... Press 'q' to quit.")


# Main Loop
# frankie keeps checking each frame for movement
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # create a mask to show where movement is
    fgmask = fgbg.apply(frame)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_DILATE, kernel)

    # find main moving areas in image
    contours, _ = cv2.findContours(
        fgmask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    label = "NO MOTION"

    if contours:
        c = max(contours, key=cv2.contourArea)

        if cv2.contourArea(c) > 2000:    # ignore small movements so it does not trigger from noise
            x, y, w, h = cv2.boundingRect(c)
            cx = x + w // 2
            area = w * h

            label = "MOVING"

            if prev_area is not None and prev_cx is not None:
                area_change = area - prev_area
                lateral_movement = abs(cx - prev_cx)

                if area_change > 1200 and lateral_movement < 60:
                    approach_count += 1
                else:
                    approach_count = max(0, approach_count - DECAY)

                if approach_count >= 5:
                    label = "APPROACHING"

                    if STATE == "IDLE":
                        STATE = "ENGAGED"
                        speak("Hi! I'm Frankie. Please return unused medicines to your pharmacy instead of putting them in the bin or sink.")

            prev_area = area
            prev_cx = cx

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    else:
        approach_count = max(0, approach_count - DECAY)

   
    # Conversation Mode
    # frankie listens once then replies using library 
    
    if STATE == "ENGAGED":

        print("Conversation started...")

        user_text = listen_once()

        # if speech was recognized, match it to a response
        if user_text:
            reply = get_reply(user_text)
            speak(reply)

            # end interaction if user says bye

            if "bye" in user_text.lower():
                speak("Goodbye! Remember to return unused medicines.")
                STATE = "IDLE"
                approach_count = 0
                time.sleep(2)

        else:
            speak("I didn't catch that.")

        # reset approach counter to prevent retriggering
        approach_count = 0


    # show detection label on screen during testing
  
    cv2.putText(
        frame,
        label,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0) if label == "APPROACHING" else (255, 255, 0),
        2
    )

    cv2.imshow("Frankie V2", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# release cam and close OpenCV window properly

cap.release()
cv2.destroyAllWindows()