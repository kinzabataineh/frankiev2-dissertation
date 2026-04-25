import cv2
import time
import subprocess
import sys


# Set up webcam and background subtraction

cap = cv2.VideoCapture(0)
fgbg = cv2.createBackgroundSubtractorMOG2(
    history=300,
    varThreshold=50,
    detectShadows=False
)

# these variables store the previous detected movement size and position
# used to compare movement between frames

prev_area = None
prev_cx = None
approach_count = 0
DECAY = 1  # lowers approach counter when movement isn't an approach

CHAT_SCRIPT = "frankie_stt_tts.py"
COOLDOWN_SECONDS = 8.0
last_trigger_time = 0.0
triggered_this_approach = False  # stops frankie triggering when same person is still close


# Main loop
# each frame is checked for motion and approach

while True:
    ret, frame = cap.read()
    if not ret:
        break

# create a foreground mask showing areas that are moving

    fgmask = fgbg.apply(frame)

    # clean up motion mask to reduce noise and random motion

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_DILATE, kernel)

# find moving region

    contours, _ = cv2.findContours(
        fgmask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    label = "NO MOTION"
    now = time.time()
    in_cooldown = (now - last_trigger_time) < COOLDOWN_SECONDS

    if contours:
        c = max(contours, key=cv2.contourArea)

        if cv2.contourArea(c) > 2000:
            x, y, w, h = cv2.boundingRect(c)
            cx = x + w // 2
            area = w * h

            label = "MOVING"

            # Approach detection logic 
            if prev_area is not None and prev_cx is not None:
                area_change = area - prev_area
                lateral_movement = abs(cx - prev_cx)

                if area_change > 1200 and lateral_movement < 60:
                    approach_count += 1
                else:
                    approach_count = max(0, approach_count - DECAY)

                # confirm approach only after several matching frames

                if approach_count >= 5:
                    label = "APPROACHING"

                    
                    if (not in_cooldown) and (not triggered_this_approach):
                        print("APPROACH CONFIRMED -> launching Frankie STT/TTS")
                        last_trigger_time = now
                        triggered_this_approach = True
                        approach_count = 0  

                        
                        cv2.destroyAllWindows()
                        cap.release()

                        # runs script when approach is confirmed

                        subprocess.run([sys.executable, CHAT_SCRIPT], check=False)

                        # to open camera again after interaction ends
                        cap = cv2.VideoCapture(0)
                        if not cap.isOpened():
                            raise RuntimeError("Could not reopen camera after Frankie.")
                        fgbg = cv2.createBackgroundSubtractorMOG2(
                            history=300,
                            varThreshold=50,
                            detectShadows=False
                        )

                        prev_area = None
                        prev_cx = None

            prev_area = area
            prev_cx = cx

            # draw box around moving person/object
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # resets so a new approach can trigger again later
            if area < 35000:   # change if needed (depending on camera distance)
                triggered_this_approach = False

    else:
        approach_count = max(0, approach_count - DECAY)
        triggered_this_approach = False

    # displays detection status
    cv2.putText(
        frame,
        label,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0) if label == "APPROACHING" else (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"approach_count={approach_count} cooldown={'ON' if in_cooldown else 'OFF'}",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow("Approach Detection", frame)
    
    # press q to stop manually
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()