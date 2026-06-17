#!/home/pepotty/miniconda3/envs/aia/bin/python
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import sys
import threading
from flask import Flask, request, jsonify, render_template, Response, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

# IMPORT DEI MODULI LOCALI MODULARI
import globals
from camera import camera_worker, stream_to_browser
from webhook import process_dialogflow_webhook
from database import salva_paziente_db, get_user, user_exists, email_exists, register_user, get_all_pazienti, calcola_triage
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

# --- AVVIO THREAD WEBCAM DAL MODULO CAMERA ---
threading.Thread(target=camera_worker, args=(model, class_names), daemon=True).start()


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
    return Response(stream_to_browser(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webhook', methods=['POST'])
def dialogflow_webhook():
    req = request.get_json(force=True)
    return process_dialogflow_webhook(req)

@app.route('/api/acquisisci', methods=['POST'])
def acquisisci():
    globals.capture_requested = True
    return jsonify({"status": "ok"})

@app.route('/api/reset', methods=['POST'])
def reset_triage():
    globals.camera_active = True
    globals.captured_image_bytes = None
    globals.capture_requested = False
    globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0}
    globals.dati_paziente = {"nome": "-", "data_nascita": "-", "sintomi": "-", "livello_dolore": "-", "codice": "-"}
    return jsonify({"status": "ok"})

@app.route('/api/stato_triage', methods=['GET'])
def stato_triage():
    # Richiamiamo il dizionario condiviso dal modulo globals
    nome = globals.dati_paziente.get('nome', '-')
    sintomi = globals.dati_paziente.get('sintomi', '-')
    data_n = globals.dati_paziente.get('data_nascita', '-')
    livello = globals.ultimo_dato_dolore.get('pain_level', '-')
    
    # Calcoliamo il codice in tempo reale basandoci sulla logica centralizzata di database.py
    if nome != "-" and sintomi != "-" and data_n != "-":
        # Usa la funzione ufficiale di database.py!
        codice_reale, _ = calcola_triage(sintomi, livello)
        globals.dati_paziente['codice'] = codice_reale
    else:
        globals.dati_paziente['codice'] = "-"

    response = jsonify({"webcam": globals.ultimo_dato_dolore, "dialogflow": globals.dati_paziente})
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/api/salva_paziente', methods=['POST'])
def salva_paziente():
    nome = globals.dati_paziente.get('nome', '-')
    data_nascita = globals.dati_paziente.get('data_nascita', '-')
    sintomi = globals.dati_paziente.get('sintomi', '-')
    livello_dolore = globals.ultimo_dato_dolore.get('pain_level', '-')
    
    if nome == "-" and livello_dolore == "-":
        return jsonify({"status": "error", "message": "Nessun dato valido da salvare."}), 400

    successo, codice, risultato = salva_paziente_db(nome, data_nascita, sintomi, livello_dolore)
    
    if successo:
        return jsonify({"status": "ok", "codice": codice, "messaggio": risultato})
    else:
        return jsonify({"status": "error", "message": risultato}), 500

@app.route('/pazienti')
def visualizza_pazienti():
    if 'utente' not in session:
        flash("Devi effettuare l'accesso per poter visualizzare l'archivio dei pazienti.", "error")
        return redirect(url_for('login'))
    pazienti = get_all_pazienti()
    return render_template('pazienti.html', pazienti=pazienti)

if __name__ == '__main__':
    print("\n--- AVVIO SERVER TRIAGE MODULARE ---")
    app.run(host='0.0.0.0', port=5000, threaded=True)