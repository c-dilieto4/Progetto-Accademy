ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0, "face_detected": False}
dati_paziente = {
    "nome": "-",
    "data_nascita": "-",
    "sintomi": "-",
    "livello_dolore": "-",
    "codice": "-",
    "codice_fiscale": "-"
}

camera_active = True
capture_requested = False
capture_in_progress = False
last_capture_error = ""
captured_image_bytes = None
current_stream_bytes = None
stream_frame_id = 0
camera_index = None
camera_width = None
camera_height = None
camera_status = "Ricerca webcam..."
camera_error = ""
paziente_salvato = False
