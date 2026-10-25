import sys

import cv2

# Adresa RTSP streamu – uprav podle typu kamery
username = "admin"
password = "TVOJE_HESLO"

url = f"rtsp://{username}:{password}@192.168.0.244:554/stream1"

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
if not cap.isOpened():
    print("Nepodařilo se připojit ke kameře.")
    sys.exit()

print("Kamera připojena. Pro ukončení stiskni Q.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Nepodařilo se načíst snímek.")
        break

    cv2.imshow("IP Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
