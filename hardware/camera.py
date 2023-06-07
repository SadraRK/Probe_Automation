import cv2

from hardware.camera_videocapture import VideoCapture

cap = VideoCapture(0)
cam = cap.cam
cv2.namedWindow("output", cv2.WINDOW_NORMAL)
_, frame = cap.read()
cv2.resizeWindow("output", 600, int((frame.shape[0] / frame.shape[1]) * 600))
cv2.moveWindow("output", 20, 20)

while True:
    _, frame = cap.read()

    cv2.imshow('output', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
