import cv2


class YuNetDetector:
    def __init__(self, model_path, confidence=0.8):
        self.detector = cv2.FaceDetectorYN.create(
            model_path,
            "",
            (320, 320),
            confidence,
            0.3,
            5000,
        )

    def detect(self, frame):
        height, width = frame.shape[:2]
        self.detector.setInputSize((width, height))
        _, faces = self.detector.detect(frame)

        if faces is None:
            return []

        return faces