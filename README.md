=============================================================
  HospitalBot - Academy DIEM 2026
  Di Lieto Christian Pio, Turi Martina, Pepe Daniele, Orsini Giovanni
=============================================================

DESCRIZIONE
-----------
HospitalBot e' un sistema di supporto decisionale al triage del pronto
soccorso che integra NLP (Dialogflow), Computer Vision (Teachable Machine)
e un backend Flask con database PostgreSQL.

=============================================================
REQUISITI DI SISTEMA
=============================================================

- Python 3.x con Anaconda (ambiente: aia_env)
- PostgreSQL installato e in esecuzione
- Account ngrok (gratuito) su https://dashboard.ngrok.com
- Account Google con agente Dialogflow configurato
- Webcam collegata al PC
- File del modello Teachable Machine (keras_model.h5 e labels.txt)
  nella cartella del progetto

=============================================================
INSTALLAZIONE DIPENDENZE (solo prima volta)
=============================================================

Aprire Anaconda Prompt e digitare:

  conda activate aia_env
  pip install flask
  pip install tensorflow==2.13.0
  pip install psycopg2-binary
  pip install opencv-python
  pip install cvlib
  pip install numpy<2
  pip install werkzeug

=============================================================
CONFIGURAZIONE DATABASE (solo prima volta)
=============================================================

1. Aprire pgAdmin
2. Creare un database chiamato: AIA_Gruppo3
3. Aprire il Query Tool sul database AIA_Gruppo3
4. Eseguire il file Create_DB.sql incluso nel progetto (tasto F5)
   oppure eseguire manualmente:

   CREATE USER www WITH PASSWORD 'www' SUPERUSER;

   CREATE TABLE pazienti_triage (
       id SERIAL PRIMARY KEY,
       nome VARCHAR(100),
       data_nascita VARCHAR(50),
       sintomi TEXT,
       livello_dolore VARCHAR(50),
       codice_assegnato VARCHAR(20),
       codice_fiscale VARCHAR(50)
   );
   GRANT ALL PRIVILEGES ON TABLE pazienti_triage TO www;
   GRANT USAGE, SELECT, UPDATE ON SEQUENCE pazienti_triage_id_seq TO www;

   CREATE TABLE utenti (
       username VARCHAR(50) PRIMARY KEY,
       nome_completo VARCHAR(100) NOT NULL,
       email VARCHAR(100) UNIQUE NOT NULL,
       pass VARCHAR(255) NOT NULL
   );
   GRANT ALL PRIVILEGES ON TABLE utenti TO www;

=============================================================
CONFIGURAZIONE NGROK (solo prima volta)
=============================================================

1. Registrarsi su https://dashboard.ngrok.com/signup
2. Copiare il proprio authtoken da:
   https://dashboard.ngrok.com/get-started/your-authtoken
3. Aprire PowerShell e digitare:
   ngrok config add-authtoken IL_PROPRIO_TOKEN

=============================================================
AVVIO DEL SISTEMA (ogni volta)
=============================================================

STEP 1 - Avviare Flask (Anaconda Prompt):

  conda activate aia_env
  cd C:\percorso\della\cartella\progetto
  python app.py

  Attendere il messaggio: "AVVIO SERVER TRIAGE MODULARE"
  Lasciare questo terminale APERTO.

STEP 2 - Avviare ngrok (PowerShell, secondo terminale):

  ngrok http 5000

  Copiare l'URL che appare, esempio:
  https://xxxx.ngrok-free.dev

STEP 3 - Configurare Dialogflow:

  1. Andare su https://dialogflow.cloud.google.com
  2. Selezionare l'agente "Triage"
  3. Cliccare su "Fulfillment" nel menu a sinistra
  4. Incollare nel campo URL:
     https://xxxx.ngrok-free.dev/webhook
     (sostituire xxxx con l'URL reale di ngrok)
  5. Cliccare Save

STEP 4 - Aprire la dashboard:

  Aprire il browser e andare su:
  http://localhost:5000

=============================================================
UTILIZZO DEL SISTEMA
=============================================================

1. Dalla dashboard, premere "Acquisisci Volto" per avviare
   l'analisi facciale tramite webcam.

2. Usare il chatbot in basso a destra per inserire i dati
   del paziente (nome, data di nascita, codice fiscale, sintomi).
   Esempio: "Sono Mario Rossi nato il 05/03/1980 CF RSSMRA80C05H501Z
             ho la febbre"

3. Il sistema assegnera' automaticamente un codice triage:
   - ROSSO: situazione urgente
   - ARANCIONE: urgenza media
   - VERDE: urgenza minore

4. Premere "Salva nel DB" per archiviare i dati del paziente.

5. Per visualizzare l'archivio pazienti:
   - Cliccare "Accedi (Area Medici)" in alto a destra
   - Registrarsi con username e password
   - Cliccare "Vedi Archivio"

=============================================================
STRUTTURA DEI FILE DEL PROGETTO
=============================================================

  app.py              - Server Flask principale e rotte API
  webhook.py          - Logica webhook Dialogflow
  database.py         - Connessione PostgreSQL e logica triage
  camera.py           - Gestione webcam e modello AI
  globals.py          - Variabili globali condivise tra moduli
  ai_model.py         - Caricamento modello Teachable Machine
  keras_model.h5      - Modello Teachable Machine addestrato
  labels.txt          - Etichette classi del modello
  Create_DB.sql       - Script creazione database
  templates/
    index.html        - Dashboard principale
    login.html        - Pagina login/registrazione medici
    pazienti.html     - Archivio storico pazienti

=============================================================
NOTE IMPORTANTI
=============================================================

- L'URL di ngrok cambia ad ogni riavvio: aggiornarlo sempre
  nella sezione Fulfillment di Dialogflow.
- PostgreSQL deve essere in esecuzione prima di avviare app.py.
- La webcam deve essere collegata e disponibile.
- Il file keras_model.h5 e labels.txt devono essere nella
  stessa cartella di app.py.

=============================================================
