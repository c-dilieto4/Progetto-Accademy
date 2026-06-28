#app.py
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import sys
import threading
from flask import Flask, request, jsonify, render_template, Response, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import globals
from camera import camera_worker, stream_to_browser, lista_camere
from webhook import process_dialogflow_webhook
from database import salva_paziente_db, get_user, user_exists, email_exists, register_user, get_all_pazienti, calcola_triage
from voice_bot import invia_testo_a_dialogflow, chiudi_sessione

# --- SETUP MODELLO AI ---
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "keras_model.h5")
labels_path = os.path.join(script_dir, "labels.txt")

try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.layers import DepthwiseConv2D
except ImportError:
    from keras.models import load_model
    from keras.layers import DepthwiseConv2D

class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, **kwargs):
        if 'groups' in kwargs:
            del kwargs['groups']
        super().__init__(**kwargs)

print("[INFO] Caricamento del modello Teachable Machine...")
try:
    model = load_model(model_path, compile=False, custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D})
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            class_names = [line.strip() for line in f.readlines()]
    else:
        class_names = ["0 Dolore Lieve", "1 Dolore Moderato", "2 Dolore Forte"]
    print("[OK] Modello caricato con successo!")
except Exception as e:
    print(f"[ERRORE] Impossibile caricare il modello Keras: {e}")
    sys.exit(1)

# --- SETUP FLASK ---
app = Flask(__name__)
app.secret_key = 'triage_secret_key_2026'

# --- SETUP SOCKETIO (per il chatbot vocale) ---
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- AVVIO THREAD WEBCAM DAL MODULO CAMERA ---
threading.Thread(target=camera_worker, args=(model, class_names), daemon=True).start()


def campo_compilato(valore):
    return bool(valore and str(valore).strip() != "-")


def socket_sid():
    return getattr(request, "sid", "")


# --- ROTTE DI AUTENTICAZIONE CLINICA ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'utente' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user_row = get_user(username)
        
        if not user_row:
            flash(f"L'username '{username}' non esiste.", "error")
            return render_template('login.html')
            
        if check_password_hash(user_row['pass'], password):
            session['utente'] = user_row['username']
            session['nome'] = user_row['nome_completo']
            session['email'] = user_row['email']
            return redirect(url_for('dashboard'))
        else:
            flash("Username o password errati.", "error")
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if user_exists(username):
        flash(f"L'username '{username}' è già in uso.", "error")
        return render_template('login.html')
    if email_exists(email):
        flash(f"L'email '{email}' è già in uso.", "error")
        return render_template('login.html')
        
    hashed_password = generate_password_hash(password)
    if register_user(username, nome, email, hashed_password):
        flash("Registrazione completata con successo. Ora puoi accedere!", "success")
    else:
        flash("Errore di Sistema nel database.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))


# --- ROTTE CORE APPLICAZIONE ---

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    response = Response(stream_to_browser(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/webhook', methods=['POST'])
def dialogflow_webhook():
    req = request.get_json(force=True)
    return process_dialogflow_webhook(req)

@app.route('/api/acquisisci', methods=['POST'])
def acquisisci():
    globals.capture_requested = True
    globals.capture_in_progress = True
    globals.last_capture_error = ""
    return jsonify({"status": "ok"})

@app.route('/api/camere', methods=['GET'])
def elenco_camere():
    forza_scan = request.args.get("scan") == "1"
    return jsonify({
        "camere": lista_camere(forza_scan=forza_scan),
        "attiva": globals.camera_index,
        "status": globals.camera_status,
        "error": globals.camera_error
    })

@app.route('/api/camera', methods=['POST'])
def seleziona_camera():
    data = request.get_json(silent=True) or {}

    try:
        indice = int(data.get('index'))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Indice camera non valido."}), 400

    if indice < 0 or indice > 20:
        return jsonify({"status": "error", "message": "Indice camera fuori intervallo."}), 400

    globals.camera_index = indice
    globals.camera_active = True
    globals.capture_requested = False
    globals.capture_in_progress = False
    globals.last_capture_error = ""
    globals.captured_image_bytes = None
    globals.current_stream_bytes = None
    globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0, "face_detected": False}
    globals.camera_status = f"Apertura camera {indice}..."
    globals.camera_error = ""
    return jsonify({"status": "ok", "index": indice})

@app.route('/api/reset', methods=['POST'])
def reset_triage():
    globals.camera_active = True
    globals.captured_image_bytes = None
    globals.capture_requested = False
    globals.capture_in_progress = False
    globals.last_capture_error = ""
    globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0, "face_detected": False}
    globals.dati_paziente = {"nome": "-", "data_nascita": "-", "sintomi": "-", "livello_dolore": "-", "codice": "-", "codice_fiscale": "-"}
    globals.paziente_salvato = False
    return jsonify({"status": "ok"})

@app.route('/api/stato_triage', methods=['GET'])
def stato_triage():
    nome = globals.dati_paziente.get('nome', '-')
    sintomi = globals.dati_paziente.get('sintomi', '-')
    data_n = globals.dati_paziente.get('data_nascita', '-')
    codice_fiscale = globals.dati_paziente.get('codice_fiscale', '-')
    livello = globals.ultimo_dato_dolore.get('pain_level', '-')
    livello_disponibile = campo_compilato(livello)
    face_detected = bool(globals.ultimo_dato_dolore.get('face_detected', False) and livello_disponibile)
    confidence = globals.ultimo_dato_dolore.get('confidence', 0.0)
    
    if all(campo_compilato(v) for v in (nome, sintomi, data_n, codice_fiscale)):
        codice_reale, _ = calcola_triage(sintomi, livello, face_detected, confidence)
        globals.dati_paziente['codice'] = codice_reale
    else:
        globals.dati_paziente['codice'] = "-"

    response = jsonify({
        "webcam": globals.ultimo_dato_dolore,
        "dialogflow": globals.dati_paziente,
        "camera": {
            "status": globals.camera_status,
            "error": globals.camera_error,
            "capture_in_progress": globals.capture_in_progress,
            "last_capture_error": globals.last_capture_error,
            "stream_frame_id": globals.stream_frame_id
        },
        "salvato": globals.paziente_salvato
    })
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/api/salva_paziente', methods=['POST'])
def salva_paziente():
    nome = globals.dati_paziente.get('nome', '-')
    data_nascita = globals.dati_paziente.get('data_nascita', '-')
    sintomi = globals.dati_paziente.get('sintomi', '-')
    livello_dolore = globals.ultimo_dato_dolore.get('pain_level', '-')
    livello_disponibile = campo_compilato(livello_dolore)
    face_detected = bool(globals.ultimo_dato_dolore.get('face_detected', False) and livello_disponibile)
    confidence = globals.ultimo_dato_dolore.get('confidence', 0.0)
    codice_fiscale = globals.dati_paziente.get('codice_fiscale', '-')
    
    if not all(campo_compilato(v) for v in (nome, data_nascita, sintomi, codice_fiscale)):
        return jsonify({"status": "error", "message": "Completa nome, data di nascita, sintomi e codice fiscale prima di salvare."}), 400

    if globals.paziente_salvato:
        codice = globals.dati_paziente.get('codice', '-')
        return jsonify({
            "status": "ok",
            "codice": codice,
            "messaggio": "Paziente gia' salvato nel database.",
            "salvato": True
        })

    successo, codice, risultato = salva_paziente_db(nome, data_nascita, sintomi, livello_dolore, codice_fiscale, face_detected, confidence)
    
    if successo:
        globals.dati_paziente['codice'] = codice
        globals.paziente_salvato = True
        return jsonify({"status": "ok", "codice": codice, "messaggio": risultato, "salvato": True})
    else:
        return jsonify({"status": "error", "message": risultato}), 500

@app.route('/pazienti')
def visualizza_pazienti():
    if 'utente' not in session:
        flash("Devi effettuare l'accesso per poter visualizzare l'archivio dei pazienti.", "error")
        return redirect(url_for('login'))
    pazienti = get_all_pazienti()
    return render_template('pazienti.html', pazienti=pazienti)


# --- EVENTI SOCKETIO PER IL CHATBOT VOCALE ---
# Il riconoscimento vocale (STT) e la sintesi (TTS) avvengono lato browser
# tramite Web Speech API. Qui riceviamo solo TESTO gia' trascritto e lo
# inviamo a Dialogflow, restituendo la risposta testuale.

@socketio.on('connect')
def handle_connect():
    print(f"[VOICE] Client connesso: {socket_sid()}")


@socketio.on('disconnect')
def handle_disconnect():
    sid = socket_sid()
    print(f"[VOICE] Client disconnesso: {sid}")
    chiudi_sessione(sid)


@socketio.on('chat_reset')
def handle_chat_reset():
    sid = socket_sid()
    print(f"[VOICE] Reset sessione Dialogflow: {sid}")
    chiudi_sessione(sid)
    emit('chat_reset_done', {'status': 'ok'})


@socketio.on('voice_text')
def handle_voice_text(data):
    """
    Riceve il testo gia' trascritto dal browser (Web Speech API),
    lo invia a Dialogflow e restituisce la risposta.
    """
    try:
        testo_utente = data.get('testo', '').strip()
        origine = data.get('origine', 'voice')
        print(f"[VOICE] Utente ha detto: {testo_utente}")

        if not testo_utente:
            emit('voice_response', {
                'testo_utente': '',
                'risposta_testo': 'Non ho sentito nulla, riprova.',
                'origine': origine
            })
            return

        risposta_testo = invia_testo_a_dialogflow(testo_utente, socket_sid())
        print(f"[VOICE] Risposta Dialogflow: {risposta_testo}")

        emit('voice_response', {
            'testo_utente': testo_utente,
            'risposta_testo': risposta_testo,
            'origine': origine
        })

    except Exception as e:
        print(f"[ERRORE VOICE] {e}")
        emit('voice_response', {
            'testo_utente': '',
            'risposta_testo': 'Errore nella comunicazione con Dialogflow.',
            'origine': data.get('origine', 'voice') if isinstance(data, dict) else 'voice'
        })


if __name__ == '__main__':
    print("\n--- AVVIO SERVER TRIAGE MODULARE ---")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
