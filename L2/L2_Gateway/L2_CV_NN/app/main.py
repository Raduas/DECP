import time

import cv2
from camera import IPCamera
from faces_db.faces_db import FaceDB
from models.face_recognition import FaceRecognizer
from models.gestures import HandGestureDetector
from models.yunet import YuNetDetector
from unlock import Unlocker


def do_unlock(name):
    print(f"ODEMČENO: {name}")
    # sem později GPIO / MQTT / HTTP volání


def main():
    camera = IPCamera(
        host="192.168.0.244",
        username="admin",
        password="TVOJE_HESLO",
        stream="/stream1",
    )

    detector = YuNetDetector(
        "weights/face_detection_yunet_2023mar.onnx",
        confidence=0.8,
    )

    detection_interval = 0.5  # 2 detekcí za sekundu
    last_detection = 0
    faces = []
    recognizer = FaceRecognizer("weights/face_recognition_sface_2021dec.onnx")
    db = FaceDB()
    labels = []

    gesture = HandGestureDetector()
    gesture_interval = 0.2
    last_gesture = 0
    horns_streak = {}  # index tváře -> počet po sobě jdoucích pozitivních snímků
    horns_flags = []

    unlocker = Unlocker(allowed={"Radek"}, action=do_unlock)

    try:
        if not camera.connect():
            raise RuntimeError("Nelze se připojit ke kameře.")

        while True:
            ret, frame = camera.read()
            if not ret:
                continue

            now = time.monotonic()

            if now - last_detection >= detection_interval:
                # Zmenšení obrazu pro rychlejší detekci
                small = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)

                detected = detector.detect(small)

                # Přepočet souřadnic na původní obraz
                sx = frame.shape[1] / 640
                sy = frame.shape[0] / 360

                faces = []
                for face in detected:
                    face = face.copy()
                    face[:4:2] *= sx
                    face[1:4:2] *= sy
                    face[4:14:2] *= sx
                    face[5:14:2] *= sy
                    faces.append(face)
                    labels = []

                    for face in faces:
                        aligned = recognizer.align(frame, face)
                        emb = recognizer.get_embedding(aligned)
                        labels.append(db.identify(recognizer, emb))

                last_detection = now

            if faces and now - last_gesture >= gesture_interval:
                horns_flags = []
                for i, face in enumerate(faces):
                    found, _ = gesture.detect(frame, face)
                    horns_streak[i] = horns_streak.get(i, 0) + 1 if found else 0
                    horns_flags.append(horns_streak[i] >= 3)  # ~0,6 s držení
                last_gesture = now
            elif not faces:
                horns_flags = []
                horns_streak.clear()

            for i, (face, (name, score)) in enumerate(zip(faces, labels)):
                x, y, w, h = face[:4].astype(int)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"{name} {score:.2f}",
                    (x, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                if i < len(horns_flags) and horns_flags[i]:
                    cv2.putText(
                        frame,
                        f"{name}: Gesto OK",
                        (x, y + h + 24),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )

            who = unlocker.update(labels, horns_flags)
            if who:
                cv2.putText(
                    frame,
                    f"ODEMCENO: {who}",
                    (x, y + h + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    3,
                )

            cv2.imshow("CV_NN", frame)
            cv2.resizeWindow("CV_NN", 1920, 1080)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord("e") and faces:
                biggest = max(faces, key=lambda f: f[2] * f[3])
                emb = recognizer.get_embedding(recognizer.align(frame, biggest))
                db.add("Radek", emb)
                print("uloženo")

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
