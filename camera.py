# camera.py
import cv2
import cvlib as cv
import numpy as np
import time
import globals

def camera_worker(model, class_names):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERRORE] Impossibile accedere alla webcam.")
        return

    frame_count = 0
    last_face_box = None

    while True:
        if not globals.camera_active:
            time.sleep(0.1)
            continue

        success, frame = cap.read()
        if not success:
            time.sleep(0.1)
            continue

        display_frame = frame.copy()

        if frame_count % 5 == 0:
            faces, confidences = cv.detect_face(frame)
            if len(faces) > 0:
                last_face_box = max(faces, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))
            else:
                last_face_box = None
        frame_count += 1

        fx1, fy1, fx2, fy2 = 0, 0, frame.shape[1], frame.shape[0]
        if last_face_box is not None:
            startX, startY, endX, endY = last_face_box
            buffer_x = int((endX - startX) * 0.25)
            buffer_y = int((endY - startY) * 0.25)
            fx1 = max(0, startX - buffer_x)
            fy1 = max(0, startY - buffer_y)
            fx2 = min(frame.shape[1], endX + buffer_x)
            fy2 = min(frame.shape[0], endY + buffer_y)
            
            cv2.rectangle(display_frame, (fx1, fy1), (fx2, fy2), (0, 255, 255), 2)
            cv2.putText(display_frame, "Volto", (fx1, fy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        if globals.capture_requested:
            globals.capture_requested = False
            
            if last_face_box is not None:
                face_crop = frame[fy1:fy2, fx1:fx2]
            else:
                face_crop = frame.copy()
            
            try:
                rgb_frame = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                resized_frame = cv2.resize(rgb_frame, (224, 224), interpolation=cv2.INTER_AREA)
                image_array = np.asarray(resized_frame, dtype=np.float32).reshape(1, 224, 224, 3)
                normalized_image = (image_array / 127.5) - 1.0

                prediction = model.predict(normalized_image)
                index = np.argmax(prediction)
                globals.ultimo_dato_dolore['pain_level'] = class_names[index]
                globals.ultimo_dato_dolore['confidence'] = float(prediction[0][index] * 100)
                print(f"[AI] Acquisizione completata. Rilevato: {class_names[index]}")
            except Exception as e:
                print(f"[ERRORE] Elaborazione AI fallita: {e}")

            ret, buffer = cv2.imencode('.jpg', face_crop)
            globals.captured_image_bytes = buffer.tobytes()
            globals.camera_active = False

        ret, buffer = cv2.imencode('.jpg', display_frame)
        globals.current_stream_bytes = buffer.tobytes()
        time.sleep(0.02)

def stream_to_browser():
    while True:
        if not globals.camera_active and globals.captured_image_bytes is not None:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + globals.captured_image_bytes + b'\r\n')
            time.sleep(0.5)
        elif globals.current_stream_bytes is not None:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + globals.current_stream_bytes + b'\r\n')
            time.sleep(0.04)
        else:
            time.sleep(0.1)