#!/home/pepotty/miniconda3/envs/aia/bin/python
import threading
# 1. AGGIORNATI GLI IMPORT DI FLASK CON LE FUNZIONI DI SESSIONE
from flask import Flask, request, jsonify, render_template, Response, session, redirect, url_for, flash
# Libreria nativa di Flask per gestire in sicurezza le password crittografate
from werkzeug.security import generate_password_hash, check_password_hash

import globals
from ai_model import load_ai_model
from camera import camera_worker, stream_to_browser
from webhook import process_dialogflow_webhook

# 2. IMPORT DELLE NUOVE FUNZIONI UTENTE DA DATABASE.PY
from database import salva_paziente_db, get_user, user_exists, email_exists, register_user

app = Flask(__name__)
# CHIAVE SEGRETA OBBLIGATORIA PER LE SESSIONI (Puoi cambiarla con una stringa a caso)
app.secret_key = 'triage_secret_key_2026'

# --- SETUP MODELLO AI ---
model, class_names = load_ai_model()

# --- AVVIO THREAD WEBCAM ---
threading.Thread(target=camera_worker, args=(model, class_names), daemon=True).start()


# --- ROTTE DI AUTENTICAZIONE ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se l'utente è già loggato, lo rimandiamo alla dashboard
    if 'utente' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user_row = get_user(username)
        
        if not user_row:
            flash(f"L'username '{username}' non esiste.", "error")
            return render_template('login.html')
            
        # Verifica l'hash della password salvata nel DB con quella inserita nel form
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
        
    # Genera l'hash sicuro della password (corrispettivo del password_hash di PHP)
    hashed_password = generate_password_hash(password)
    
    if register_user(username, nome, email, hashed_password):
        flash("Registrazione completata con successo. Ora puoi accedere!", "success")
    else:
        flash("Errore di Sistema nel database.", "error")
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- ROTTE APPLICAZIONE (ACCESSIBILE A TUTTI) ---

@app.route('/')
def dashboard():
    # Ora la dashboard è libera, non c'è più il redirect forzato al login
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


# --- ROTTA ARCHIVIO DATI (PROTETTA: SOLO UTENTI REGISTRATI) ---

# Ricordati di aggiungere get_all_pazienti negli import in alto da database
from database import salva_paziente_db, get_user, user_exists, email_exists, register_user, get_all_pazienti

@app.route('/pazienti')
def visualizza_pazienti():
    # Solo gli utenti autenticati possono visualizzare lo storico dei dati
    if 'utente' not in session:
        flash("Devi effettuare l'accesso per poter visualizzare l'archivio dei pazienti.", "error")
        return redirect(url_for('login'))
    
    pazienti = get_all_pazienti()
    return render_template('pazienti.html', pazienti=pazienti)

if __name__ == '__main__':
    print("\n--- AVVIO SERVER TRIAGE ---")
    app.run(host='0.0.0.0', port=5000, threaded=True)