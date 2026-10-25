import cv2


class FaceRecognizer:
    # Doporučený práh z dokumentace OpenCV pro kosinovou podobnost
    COSINE_THRESHOLD = 0.363

    def __init__(self, model_path):
        self.model = cv2.FaceRecognizerSF.create(model_path, "")

    def align(self, frame, face):
        # face = řádek z YuNetu (15 hodnot) v souřadnicích předaného frame
        return self.model.alignCrop(frame, face)

    def get_embedding(self, aligned_face):
        return self.model.feature(aligned_face)  # tvar (1, 128)

    def compare(self, e1, e2):
        return self.model.match(e1, e2, cv2.FaceRecognizerSF_FR_COSINE)