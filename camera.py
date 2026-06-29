# camera.py
import os
import cv2
import time
import threading
import numpy as np
import cvlib as cv
import globals

MAX_CAMERA_INDEX = 8
CAMERA_SCAN_TTL = 10
DEFAULT_CAMERA_INDEX = 4

_camera_scan_lock = threading.Lock()
_camera_cache = []
_camera_cache_time = 0.0


def crea_capture(indice):
    if os.name == "nt":
        try:
            cap = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
            if cap.isOpened():
                return cap
            cap.release()
        except cv2.error:
            pass
    return cv2.VideoCapture(indice)


def indici_camera(indice_preferito=None):
    if indice_preferito is not None:
        return [indice_preferito]

    indice_env = os.environ.get("CAMERA_INDEX")
    if indice_env is not None:
        try:
            return [int(indice_env)]
        except ValueError:
            print(f"[WARN] CAMERA_INDEX non valido: {indice_env}")

    return list(range(MAX_CAMERA_INDEX))


def prova_camera(indice):
    try:
        cap = crea_capture(indice)
    except cv2.error:
        return False, None

    try:
        if not cap.isOpened():
            return False, None

        try:
            ok, frame = cap.read()
        except cv2.error:
            return False, None

        if not ok or frame is None:
            return False, None

        return True, frame.shape
    finally:
        try:
            cap.release()
        except cv2.error:
            pass


def camera_attiva_entry():
    if globals.camera_index is None:
        return None

    return {
        "index": globals.camera_index,
        "label": f"Camera {globals.camera_index}",
        "width": globals.camera_width,
        "height": globals.camera_height,
        "active": True
    }


def aggiorna_camera_attiva(camere):
    attiva = camera_attiva_entry()
    if attiva is None:
        return camere

    altre = [camera for camera in camere if camera.get("index") != attiva["index"]]
    return [attiva] + altre


def lista_camere(forza_scan=False):
    global _camera_cache, _camera_cache_time

    now = time.time()
    if not forza_scan:
        if _camera_cache and now - _camera_cache_time < CAMERA_SCAN_TTL:
            return aggiorna_camera_attiva(_camera_cache)

        attiva = camera_attiva_entry()
        if attiva is not None:
            return [attiva]

    if not _camera_scan_lock.acquire(blocking=False):
        if _camera_cache:
            return aggiorna_camera_attiva(_camera_cache)
        attiva = camera_attiva_entry()
        return [attiva] if attiva is not None else []

    camere = []
    indice_attivo = globals.camera_index

    try:
        attiva = camera_attiva_entry()
        if attiva is not None:
            camere.append(attiva)

        for indice in range(MAX_CAMERA_INDEX):
            if indice == indice_attivo:
                continue

            ok, shape = prova_camera(indice)
            if ok:
                camere.append({
                    "index": indice,
                    "label": f"Camera {indice}",
                    "width": int(shape[1]),
                    "height": int(shape[0]),
                    "active": globals.camera_index == indice
                })

        _camera_cache = camere
        _camera_cache_time = now
        return camere
    finally:
        _camera_scan_lock.release()


def apri_camera(indice_preferito=None):
    for indice in indici_camera(indice_preferito):
        try:
            cap = crea_capture(indice)
        except cv2.error:
            continue

        if cap.isOpened():
            try:
                ok, frame = cap.read()
            except cv2.error:
                ok, frame = False, None
            if ok:
                globals.camera_index = indice
                globals.camera_width = int(frame.shape[1]) if frame is not None else None
                globals.camera_height = int(frame.shape[0]) if frame is not None else None
                globals.camera_status = f"Camera {indice} attiva"
                globals.camera_error = ""
                print(f"[OK] Webcam attiva su indice {indice}.")
                return cap, indice
        try:
            cap.release()
        except cv2.error:
            pass

    globals.camera_status = "Nessuna camera disponibile"
    globals.camera_error = "Impossibile accedere alla webcam."
    return None, None


# Recupera il modello pre-caricato dal modulo principale
def camera_worker(model, class_names):
    cap, indice_attivo = apri_camera(globals.camera_index)
    if cap is None:
        print("[ERRORE] Impossibile accedere alla webcam.")

    frame_count = 0
    last_face_box = None

    while True:
        if cap is None:
            cap, indice_attivo = apri_camera(globals.camera_index)
            if cap is None:
                time.sleep(0.5)
                continue

        if globals.camera_index is not None and globals.camera_index != indice_attivo:
            if cap is not None:
                cap.release()
            globals.current_stream_bytes = None
            globals.captured_image_bytes = None
            globals.camera_active = True
            globals.camera_status = f"Apertura camera {globals.camera_index}..."
            cap, indice_attivo = apri_camera(globals.camera_index)
            frame_count = 0
            last_face_box = None
            if cap is None:
                time.sleep(0.5)
                continue

        if not globals.camera_active:
            time.sleep(0.1)
            continue

        try:
            success, frame = cap.read()
        except cv2.error as e:
            globals.camera_status = f"Camera {indice_attivo} errore"
            globals.camera_error = str(e)
            cap.release()
            cap = None
            time.sleep(0.5)
            continue

        if not success:
            globals.camera_status = f"Camera {indice_attivo} senza segnale"
            time.sleep(0.1)
            continue
        globals.camera_status = f"Camera {indice_attivo} attiva"
        globals.camera_error = ""
        globals.camera_width = int(frame.shape[1])
        globals.camera_height = int(frame.shape[0])

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
            try:
                globals.capture_in_progress = True
                globals.last_capture_error = ""

                # Forza un controllo immediato sul frame attuale per evitare falsi positivi
                # causati dalla cache di detect_face (eseguito ogni 5 frame).
                faces_now, _ = cv.detect_face(frame)
                if len(faces_now) > 0:
                    current_face_box = max(faces_now, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))
                    face_detected = True
                    startX, startY, endX, endY = current_face_box
                    buffer_x = int((endX - startX) * 0.25)
                    buffer_y = int((endY - startY) * 0.25)
                    fx1_c = max(0, startX - buffer_x)
                    fy1_c = max(0, startY - buffer_y)
                    fx2_c = min(frame.shape[1], endX + buffer_x)
                    fy2_c = min(frame.shape[0], endY + buffer_y)
                    face_crop = frame[fy1_c:fy2_c, fx1_c:fx2_c]
                else:
                    face_detected = False
                    face_crop = frame.copy()

                globals.ultimo_dato_dolore['face_detected'] = face_detected

                rgb_frame = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                resized_frame = cv2.resize(rgb_frame, (224, 224), interpolation=cv2.INTER_AREA)
                image_array = np.asarray(resized_frame, dtype=np.float32).reshape(1, 224, 224, 3)
                normalized_image = (image_array / 127.5) - 1.0

                prediction = model.predict(normalized_image)
                index = np.argmax(prediction)
                globals.ultimo_dato_dolore['pain_level'] = class_names[index]
                globals.ultimo_dato_dolore['confidence'] = float(prediction[0][index] * 100)
                print(f"[AI] Acquisizione completata. Rilevato: {class_names[index]}")

                ret, buffer = cv2.imencode('.jpg', face_crop)
                if ret:
                    globals.captured_image_bytes = buffer.tobytes()
            except Exception as e:
                globals.last_capture_error = str(e)
                print(f"[ERRORE] Elaborazione AI fallita: {e}")
            finally:
                globals.capture_in_progress = False

        ret, buffer = cv2.imencode('.jpg', display_frame)
        if ret:
            globals.current_stream_bytes = buffer.tobytes()
            globals.stream_frame_id += 1
        time.sleep(0.02)

def stream_to_browser():
    while True:
        if globals.current_stream_bytes is not None:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + globals.current_stream_bytes + b'\r\n')
            time.sleep(0.04)
        elif globals.captured_image_bytes is not None:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + globals.captured_image_bytes + b'\r\n')
            time.sleep(0.1)
        else:
            time.sleep(0.1)
