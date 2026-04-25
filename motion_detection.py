import cv2

cap = cv2.VideoCapture(0)
fgbg = cv2.createBackgroundSubtractorMOG2()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    fgmask = fgbg.apply(frame)

    cv2.imshow("Original Camera", frame)
    cv2.imshow("Motion Mask", fgmask) # show detected motion

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# clean up camera and windows 
cap.release()
cv2.destroyAllWindows()
