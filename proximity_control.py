import cv2
import time
import subprocess
import sys


THRESH_AREA_RATIO = 0.05    
HOLD_FRAMES = 2              
COOLDOWN_SECONDS = 6.0       
MIN_CONTOUR_AREA_PX = 800    


CHAT_SCRIPT = "frankie_stt_tts.py"

def launch_chat():
    """Launch your existing STT/TTS script in the same Python environment."""
    py = sys.executable
    subprocess.run([py, CHAT_SCRIPT], check=False)

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera (index 0).")

    bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=25, detectShadows=False)

    close_count = 0
    last_trigger = 0.0

    print("=== Frankie PROXIMITY-ONLY CONTROL ===")
    print("Press 'q' in the video window to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        h, w = frame.shape[:2]
        frame_area = float(h * w)

        fg = bg.apply(frame)
        fg = cv2.dilate(fg, None, iterations=2)

        contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        area_ratio = 0.0
        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) >= MIN_CONTOUR_AREA_PX:
                x, y, bw, bh = cv2.boundingRect(c)
                area_ratio = (bw * bh) / frame_area

                # draws bounding box around detected contours
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
                cv2.putText(frame, f"prox={area_ratio:.3f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        now = time.time()
        in_cooldown = (now - last_trigger) < COOLDOWN_SECONDS

        # proximity-only rule 
        is_close = area_ratio >= THRESH_AREA_RATIO

        if is_close and not in_cooldown:
            close_count += 1
        else:
            close_count = 0

        cv2.putText(frame, f"count={close_count}/{HOLD_FRAMES}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"cooldown={'ON' if in_cooldown else 'OFF'}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # after triggering it runs the speech
        if close_count >= HOLD_FRAMES:
            print("TRIGGER (proximity-only control) -> launching STT/TTS")
            last_trigger = now
            close_count = 0

            # to pause camera during interaction to avoid triggering again
            cv2.destroyAllWindows()
            cap.release()

            launch_chat()

            # directly opens camera again after convo ends
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("Could not reopen camera after STT/TTS ended.")
            bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=25, detectShadows=False)

        cv2.imshow("Frankie Control: Proximity Only", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()