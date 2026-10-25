import cv2
import mediapipe as mp
import numpy as np


class HandGestureDetector:
    def __init__(self, max_hands=1):
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=True,   # ROI se mění, tracking by nedržel
            max_num_hands=max_hands,
            model_complexity=0,       # lite model, na Pi4 stačí
            min_detection_confidence=0.6,
        )

    @staticmethod
    def face_roi(face, frame_shape, kx=3.0, ky=2.5):
        x, y, w, h = face[:4]
        cx, cy = x + w / 2, y + h / 2
        rw, rh = w * kx, h * ky
        H, W = frame_shape[:2]
        x0 = int(max(0, cx - rw / 2))
        y0 = int(max(0, cy - rh * 0.65))  # víc prostoru nahoru
        x1 = int(min(W, cx + rw / 2))
        y1 = int(min(H, cy + rh * 0.35))
        return x0, y0, x1, y1

    @staticmethod
    def _dist(a, b):
        return np.hypot(a.x - b.x, a.y - b.y)

    def _extended(self, lm, tip, pip):
        # nezávislé na orientaci ruky: špička je dál od zápěstí než PIP kloub
        return self._dist(lm[tip], lm[0]) > self._dist(lm[pip], lm[0])

    def is_horns(self, lm):
        return (
            self._extended(lm, 8, 6)        # ukazováček
            and self._extended(lm, 20, 18)  # malíček
            and not self._extended(lm, 12, 10)  # prostředník
            and not self._extended(lm, 16, 14)  # prsteník
        )

    def detect(self, frame, face):
        """Vrací (je_paroháč, roi) pro ruku v okolí dané tváře."""
        x0, y0, x1, y1 = self.face_roi(face, frame.shape)
        if x1 - x0 < 64 or y1 - y0 < 64:
            return False, (x0, y0, x1, y1)


        crop = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
        result = self.hands.process(crop)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                if self.is_horns(hand.landmark):
                    return True, (x0, y0, x1, y1)
        return False, (x0, y0, x1, y1)