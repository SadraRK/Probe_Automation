import cv2

from hardware.camera_videocapture import VideoCapture


class FlirCamera(object):
    def __init__(self):
        self.video = VideoCapture(0)

    def __iter__(self):
        return self

    def close(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    __next__ = get_frame
