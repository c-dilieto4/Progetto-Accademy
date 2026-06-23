=============================================================
  HospitalBot - Architettura Multimodale per il Triage
  Gruppo 03 - Academy DIEM 2026
  Di Lieto Christian Pio, Turi Martina, Pepe Daniele, Orsini Giovanni
=============================================================

DESCRIZIONE
-----------
HospitalBot e' un sistema di supporto decisionale al triage del pronto
soccorso che integra:
- NLP tramite Google Dialogflow (raccolta dati anagrafici e sintomi,
  sia in chat testuale che vocale)
- Computer Vision tramite Teachable Machine (analisi espressione facciale)
- Chatbot vocale in tempo reale via browser (microfono + sintesi vocale)
- Backend Flask con WebSocket (Flask-SocketIO) e database PostgreSQL
- Dashboard web in tempo reale con archivio pazienti e autenticazione medici

=============================================================
REQUISITI
=============================================================

- Python 3.x
- PostgreSQL
- ngrok
- Agente Dialogflow configurato (https://dialogflow.cloud.google.com)
- Service Account Google con ruolo "Dialogflow API Client" (per il
  chatbot vocale, vedi sezione dedicata sotto)
- Webcam collegata al PC
- Microfono collegato al PC
- Browser Chrome o Edge (richiesti per il riconoscimento vocale
  Web Speech API)
- File del modello Teachable Machine: keras_model.h5 e labels.txt
  nella stessa cartella di app.py

Librerie Python richieste:
  flask
  flask-socketio
  tensorflow==2.13.0
  psycopg2-binary
  opencv-python
  cvlib
  numpy<2
  werkzeug
  google-cloud-dialogflow

Installazione:
  pip install flask flask-socketio tensorflow==2.13.0 psycopg2-binary opencv-python cvlib werkzeug google-cloud-dialogflow
  pip install "numpy<2" --force-reinstall

=============================================================
CONFIGURAZIONE DATABASE (solo prima volta)
=============================================================

1. Aprire pgAdmin
2. Creare il database:

   CREATE DATABASE "AIA_Gruppo3";

3. Aprire il Query Tool sul database AIA_Gruppo3 appena creato
4. Eseguire il file Create_DB.sql incluso nel progetto (tasto F5)
   per creare le tabelle e l'utente necessari.

=============================================================
CONFIGURAZIONE NGROK (solo prima volta)
=============================================================

  ngrok config add-authtoken IL_PROPRIO_TOKEN

  (il token si trova nella propria dashboard ngrok, sezione
  "Your Authtoken": https://dashboard.ngrok.com/get-started/your-authtoken)

=============================================================
CONFIGURAZIONE SERVICE ACCOUNT GOOGLE (per il chatbot vocale)
=============================================================

Necessario per permettere al backend di comunicare con l'API di
Dialogflow durante le sessioni vocali via WebSocket.

1. Andare su https://console.cloud.google.com
2. Selezionare il progetto collegato all'agente Dialogflow
   (Project ID visibile su Dialogflow > icona ingranaggio > General)
3. Andare su IAM e amministrazione > Service account
4. Cliccare "+ Crea service account", assegnare un nome
   (es. hospitalbot-voice)
5. Assegnare il ruolo "Dialogflow API Client"
6. Cliccare sul service account creato > tab "Chiavi"
7. Cliccare "Aggiungi chiave" > "Crea nuova chiave" > formato JSON
8. Rinominare il file scaricato in: service_account.json
9. Posizionare il file service_account.json nella stessa cartella
   di app.py

Nota: il Project ID dell'agente e' configurato direttamente nel
file voice_bot.py (variabile PROJECT_ID).

=============================================================
AVVIO DEL SISTEMA (ogni volta)
=============================================================

STEP 1 - Avviare Flask:

  cd C:\percorso\della\cartella\progetto
  python app.py

  Attendere il messaggio: "--- AVVIO SERVER TRIAGE MODULARE ---"
  Lasciare questo terminale APERTO.

STEP 2 - Avviare ngrok (secondo terminale):

  ngrok http 5000

  Copiare l'URL che appare, esempio: https://xxxx.ngrok-free.dev
  ATTENZIONE: l'URL cambia ad ogni riavvio di ngrok!

STEP 3 - Aggiornare Dialogflow:

  1. Andare su https://dialogflow.cloud.google.com
  2. Selezionare l'agente "Triage"
  3. Cliccare "Fulfillment" nel menu a sinistra
  4. Incollare nel campo URL:
     https://xxxx.ngrok-free.dev/webhook
     (sostituire xxxx con l'URL reale di ngrok)
  5. Cliccare Save

STEP 4 - Aprire la dashboard:

  Aprire il browser (Chrome o Edge) e andare su:
  http://localhost:5000

=============================================================
UTILIZZO - MODALITA' TESTO (chat scritta)
=============================================================

1. Premere "Acquisisci Volto" per avviare l'analisi facciale
   tramite webcam.

2. Usare il chatbot testuale (widget in basso a destra) per
   inserire i dati del paziente. Esempio di frase completa:
   "Sono Mario Rossi nato il 05/03/1980
    CF RSSMRA80C05H501Z ho la febbre"

   E' possibile modificare i dati ("cambia il mio nome in...",
   "i miei sintomi sono...") o annullare la registrazione
   ("annulla").

3. Il sistema assegna automaticamente il codice triage:
   - ROSSO:     situazione urgente
   - ARANCIONE: urgenza media
   - VERDE:     urgenza minore

   Logica: 70% peso ai sintomi dichiarati, 30% all'analisi
   visiva (Teachable Machine). Tre o piu' sintomi dello stesso
   livello incrementano automaticamente il codice assegnato.

4. Premere "Salva nel DB" per archiviare i dati del paziente
   nel database.

5. Per l'archivio pazienti:
   - Cliccare "Accedi (Area Medici)" in alto a destra
   - Registrarsi con nome, email, username e password
   - Cliccare "Archivio"
   - Usare la barra di ricerca e i filtri per codice colore

=============================================================
UTILIZZO - MODALITA' VOCALE (chatbot vocale)
=============================================================

1. Dalla dashboard, cliccare il pulsante "🎤 Parla con
   l'assistente" in alto.

2. Attendere l'attivazione del microfono (il pulsante diventa
   rosso e pulsante con la scritta "Sto ascoltando...").

3. Parlare in modo chiaro e diretto. Esempi efficaci:
   - "sono Mario Rossi"
   - "ho la febbre e la tosse"
   - "sette marzo duemilaottanta"
   - "codice fiscale RSSMRA80C05H501Z"

4. Il sistema:
   - trascrive la voce nel browser (Web Speech API)
   - invia il testo a Dialogflow tramite WebSocket
   - mostra la trascrizione e la risposta nel box sotto la
     barra superiore
   - legge ad alta voce la risposta dell'assistente (sintesi
     vocale nativa del browser)

5. Per modificare un dato a voce, usare frasi brevi e dirette
   (es. "cambia sintomo mal di testa", "mi chiamo Mario Rossi")
   per migliorare l'affidabilita' del riconoscimento.

6. Il resto del flusso (analisi facciale, calcolo codice
   triage, salvataggio nel database) e' identico alla modalita'
   testo: i dati raccolti via voce confluiscono nello stesso
   stato condiviso della dashboard.

=============================================================
STRUTTURA DEI FILE DEL PROGETTO
=============================================================

  app.py                Server Flask principale, rotte API ed
                         eventi WebSocket per il chatbot vocale
  webhook.py             Logica del webhook Dialogflow (testo e voce)
  voice_bot.py           Comunicazione testuale con l'API Dialogflow
                         per le sessioni vocali
  database.py            Connessione PostgreSQL e logica di triage
  camera.py              Gestione webcam e modello Teachable Machine
  globals.py             Variabili globali condivise tra i moduli
  ai_model.py            Caricamento del modello Teachable Machine
  keras_model.h5         Modello Teachable Machine addestrato
  labels.txt             Etichette delle classi del modello
  service_account.json   Chiave del Service Account Google (da creare,
                          vedi sezione dedicata)
  Create_DB.sql          Script di creazione tabelle e utente database
  templates/
    index.html           Dashboard principale (testo + voce + webcam)
    login.html            Pagina di login/registrazione medici
    pazienti.html         Archivio storico pazienti con filtri e ricerca

=============================================================
NOTE IMPORTANTI
=============================================================

- L'URL di ngrok cambia ad ogni riavvio: aggiornarlo sempre
  nella sezione Fulfillment di Dialogflow.
- PostgreSQL deve essere attivo prima di avviare app.py.
- Webcam e microfono devono essere collegati e abilitati nel
  browser (Chrome/Edge chiedono il permesso al primo utilizzo).
- keras_model.h5 e labels.txt devono stare nella stessa cartella
  di app.py.
- service_account.json deve stare nella stessa cartella di
  app.py e non va condiviso pubblicamente.
- Il chatbot vocale richiede una connessione internet attiva
  (per le chiamate API a Dialogflow) anche se il riconoscimento
  vocale avviene localmente nel browser.

=============================================================
