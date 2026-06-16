#!/home/pepotty/miniconda3/envs/aia/bin/python
import threading
from flask import Flask, request, jsonify, render_template, Response

import globals
from ai_model import load_ai_model
from camera import camera_worker, stream_to_browser
from webhook import process_dialogflow_webhook
from database import salva_paziente_db

app = Flask(__name__)

# --- SETUP MODELLO AI ---
model, class_names = load_ai_model()

# --- AVVIO THREAD WEBCAM ---
threading.Thread(target=camera_worker, args=(model, class_names), daemon=True).start()

# --- ROTTE FLASK ---
@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(stream_to_browser(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
    globals.dati_paziente = {"nome": "-", "data_nascita": "-", "sintomi": "-", "livello_dolore": "-"}
    return jsonify({"status": "ok"})

@app.route('/api/stato_triage', methods=['GET'])
def stato_triage():
    response = jsonify({"webcam": globals.ultimo_dato_dolore, "dialogflow": globals.dati_paziente})
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/webhook', methods=['POST'])
def dialogflow_webhook():
    req = request.get_json(force=True)
    return process_dialogflow_webhook(req)

@app.route('/api/salva_paziente', methods=['POST'])
def salva_paziente():
    # Recuperiamo i dati centralizzati in globals
    nome = globals.dati_paziente.get('nome', '-')
    data_nascita = globals.dati_paziente.get('data_nascita', '-')
    sintomi = globals.dati_paziente.get('sintomi', '-')
    livello_dolore = globals.ultimo_dato_dolore.get('pain_level', '-')
    
    if nome == "-" and livello_dolore == "-":
        return jsonify({"status": "error", "message": "Nessun dato valido da salvare."}), 400

    # Invochiamo il modulo database che calcola il codice e salva
    successo, codice, risultato = salva_paziente_db(nome, data_nascita, sintomi, livello_dolore)
    
    if successo:
        return jsonify({
            "status": "ok", 
            "codice": codice, 
            "messaggio": risultato
        })
    else:
        return jsonify({"status": "error", "message": risultato}), 500

if __name__ == '__main__':
    print("\n--- AVVIO SERVER TRIAGE ---")
    app.run(host='0.0.0.0', port=5000, threaded=True)