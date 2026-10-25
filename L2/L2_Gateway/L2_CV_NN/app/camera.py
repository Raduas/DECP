from urllib.parse import quote

import cv2


class IPCamera:
    def __init__(
        self,
        host,
        username,
        password,
        stream="/stream1",
        port=554,
    ):
        self.url = (
            f"rtsp://{quote(username, safe='')}:"
            f"{quote(password, safe='')}@{host}:{port}{stream}"
        )
        self.cap = None

    def connect(self):
        self.release()
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        return self.cap.isOpened()

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None