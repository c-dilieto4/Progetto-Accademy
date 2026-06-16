# database.py
import psycopg2

# --- LISTE SINTOMI ---
SINTOMI_GRAVI = ['dolore al petto', 'difficoltà respiratorie', 'difficoltà respiratoria', 
                 'respiro affannoso', 'perdita di coscienza', 'paralisi', 'convulsioni']
SINTOMI_MEDI = ['febbre', 'nausea', 'vomito', 'vertigini', 'mal di stomaco']
SINTOMI_LIEVI = ['mal di testa', 'tosse', 'raffreddore', 'stanchezza']

def calcola_triage(sintomi, livello_dolore=None):
    """
    Logica di triage basata esclusivamente sulla gravità dei sintomi.
    Se sono presenti più sintomi, viene data priorità al più grave.
    """
    sintomi_str = str(sintomi).lower() if sintomi else ""

    ha_sintomi_gravi = any(s in sintomi_str for s in SINTOMI_GRAVI)
    ha_sintomi_medi = any(s in sintomi_str for s in SINTOMI_MEDI)
    ha_sintomi_lievi = any(s in sintomi_str for s in SINTOMI_LIEVI)

    # Priorità: sintomi gravi hanno sempre la precedenza
    if ha_sintomi_gravi:
        return "ROSSO", "Situazione urgente! Ti prego di sederti, avviso immediatamente il personale medico."
    elif ha_sintomi_medi:
        return "ARANCIONE", "Situazione moderata. Siediti in sala d'attesa, sarai visitato a breve."
    elif ha_sintomi_lievi:
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
    Calcola il codice triage in base ai sintomi e inserisce il record nel database.
    """
    codice_assegnato, messaggio_operatore = calcola_triage(sintomi)
    
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
        
        print(f"[DB] Paziente salvato: {nome} | Codice: {codice_assegnato}")
        return True, codice_assegnato, messaggio_operatore

    except Exception as e:
        print(f"[ERRORE DB] {e}")
        return False, None, str(e)


# =====================================================================
# GESTIONE AUTENTICAZIONE UTENTI
# =====================================================================

def get_user(username):
    """Recupera i dati di un utente basandosi sullo username."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT username, nome_completo, email, pass FROM utenti WHERE username = %s;", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return {
                'username': row[0],
                'nome_completo': row[1],
                'email': row[2],
                'pass': row[3]
            }
        return None

    except Exception as e:
        print(f"[ERRORE DB GET_USER] {e}")
        return None


def user_exists(username):
    """Verifica se uno username è già registrato."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT username FROM utenti WHERE username = %s;", (username,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists

    except Exception as e:
        print(f"[ERRORE DB USER_EXISTS] {e}")
        return False


def email_exists(email):
    """Verifica se un'email è già registrata."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT email FROM utenti WHERE email = %s;", (email,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists

    except Exception as e:
        print(f"[ERRORE DB EMAIL_EXISTS] {e}")
        return False


def register_user(username, nome, email, hashed_password):
    """Registra un nuovo utente nel database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO utenti (username, nome_completo, email, pass) VALUES (%s, %s, %s, %s);",
            (username, nome, email, hashed_password)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERRORE DB REGISTER_USER] {e}")
        return False