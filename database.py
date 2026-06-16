# database.py
import psycopg2

# --- LISTE SINTOMI ---
SINTOMI_GRAVI = ['dolore al petto', 'difficoltà respiratorie', 'difficoltà respiratoria', 
                 'respiro affannoso', 'perdita di coscienza', 'paralisi', 'convulsioni']
SINTOMI_MEDI = ['febbre', 'nausea', 'vomito', 'vertigini', 'mal di stomaco']
SINTOMI_LIEVI = ['mal di testa', 'tosse', 'raffreddore', 'stanchezza']

def calcola_triage(sintomi, livello_dolore):
    """
    Logica di triage: analizza stringhe e assegna codice colore e messaggio.
    """
    sintomi_str = str(sintomi).lower() if sintomi else ""
    dolore = str(livello_dolore).lower() if livello_dolore else ""

    ha_sintomi_gravi = any(s in sintomi_str for s in SINTOMI_GRAVI)
    ha_sintomi_medi = any(s in sintomi_str for s in SINTOMI_MEDI)

    # Il controllo gestisce sia "alto/medio/basso" sia "forte/moderato/lieve" del modello AI
    if "alto" in dolore or "forte" in dolore or ha_sintomi_gravi:
        return "ROSSO", "Situazione urgente! Ti prego di sederti, avviso immediatamente il personale medico."
    elif "medio" in dolore or "moderato" in dolore or ha_sintomi_medi:
        return "ARANCIONE", "Situazione moderata. Siediti in sala d'attesa, sarai visitato a breve."
    elif "basso" in dolore or "lieve" in dolore:
        return "VERDE", "Situazione lieve. Accomodati in sala d'attesa, verrai chiamato a breve."
    else:
        return "BIANCO", "Non ho rilevato urgenze particolari. Accomodati, uno sportello ti assisterà."

# --- CONFIGURAZIONE POSTGRESQL ---
DB_CONFIG = {
    'dbname': 'AIA_Gruppo3',
    'user': 'www',
    'password': 'www',
    'host': 'localhost',
    'port': '5432'
}

def salva_paziente_db(nome, data_nascita, sintomi, livello_dolore):
    """
    Calcola il codice e inserisce il record all'interno di pgAdmin
    """
    # Esegue il calcolo del codice prima del salvataggio
    codice_assegnato, messaggio_operatore = calcola_triage(sintomi, livello_dolore)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = """
            INSERT INTO pazienti_triage (nome, data_nascita, sintomi, livello_dolore, codice_assegnato)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(query, (nome, data_nascita, sintomi, livello_dolore, codice_assegnato))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, codice_assegnato, messaggio_operatore
    except Exception as e:
        print(f"[ERRORE DB] {e}")
        return False, None, str(e)