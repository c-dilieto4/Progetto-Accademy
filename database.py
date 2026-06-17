# database.py
import psycopg2

SINTOMI_GRAVI = ['dolore al petto', 'difficoltà respiratorie', 'difficoltà respiratoria',
                 'respiro affannoso', 'perdita di coscienza', 'paralisi', 'convulsioni']
SINTOMI_MEDI = ['febbre', 'nausea', 'vomito', 'vertigini', 'mal di stomaco']
SINTOMI_LIEVI = ['mal di testa', 'tosse', 'raffreddore', 'stanchezza']

def calcola_triage(sintomi, livello_dolore=None):
    sintomi_str = str(sintomi).lower() if sintomi else ""
    dolore_str = str(livello_dolore).lower() if livello_dolore else ""

    ha_sintomi_gravi = any(s in sintomi_str for s in SINTOMI_GRAVI)
    ha_sintomi_medi = any(s in sintomi_str for s in SINTOMI_MEDI)
    ha_sintomi_lievi = any(s in sintomi_str for s in SINTOMI_LIEVI)

    teachable_alto = "alto" in dolore_str or "forte" in dolore_str
    teachable_moderato = "moderato" in dolore_str or "medio" in dolore_str
    teachable_basso = "basso" in dolore_str or "lieve" in dolore_str

    print(f"[TRIAGE] Sintomi: gravi={ha_sintomi_gravi}, medi={ha_sintomi_medi}, lievi={ha_sintomi_lievi}")
    print(f"[TRIAGE] Teachable: alto={teachable_alto}, moderato={teachable_moderato}, basso={teachable_basso}")

    if ha_sintomi_gravi or teachable_alto:
        return "ROSSO", "Situazione urgente! Ti prego di sederti, avviso immediatamente il personale medico."
    elif ha_sintomi_medi or teachable_moderato:
        return "ARANCIONE", "Situazione moderata. Siediti in sala d'attesa, sarai visitato a breve."
    else:
        return "VERDE", "Situazione lieve. Accomodati in sala d'attesa, verrai chiamato a breve."

DB_CONFIG = {
    'dbname': 'AIA_Gruppo3',
    'user': 'www',
    'password': 'www',
    'host': 'localhost',
    'port': '5432'
}

def salva_paziente_db(nome, data_nascita, sintomi, livello_dolore, codice_fiscale):
    codice_assegnato, messaggio_operatore = calcola_triage(sintomi, livello_dolore)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = """
            INSERT INTO pazienti_triage (nome, data_nascita, sintomi, livello_dolore, codice_assegnato, codice_fiscale)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (nome, data_nascita, sintomi, livello_dolore, codice_assegnato, codice_fiscale))
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DB] Paziente salvato: {nome} | CF: {codice_fiscale} | Codice: {codice_assegnato}")
        return True, codice_assegnato, messaggio_operatore
    except Exception as e:
        print(f"[ERRORE DB] {e}")
        return False, None, str(e)

def get_user(username):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT username, nome_completo, email, pass FROM utenti WHERE username = %s;", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {'username': row[0], 'nome_completo': row[1], 'email': row[2], 'pass': row[3]}
        return None
    except Exception as e:
        print(f"[ERRORE DB GET_USER] {e}")
        return None

def user_exists(username):
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

def get_all_pazienti():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, data_nascita, sintomi, livello_dolore, codice_assegnato, codice_fiscale
            FROM pazienti_triage ORDER BY id DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERRORE DB GET_ALL_PAZIENTI] {e}")
        return []