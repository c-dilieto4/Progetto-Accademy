# database.py
import psycopg2

SINTOMI_GRAVI = ['dolore al petto', 'difficoltà respiratorie', 'difficoltà respiratoria',
                 'respiro affannoso', 'perdita di coscienza', 'paralisi', 'convulsioni']
SINTOMI_MEDI = ['febbre', 'nausea', 'vomito', 'vertigini', 'mal di stomaco']
SINTOMI_LIEVI = ['mal di testa', 'tosse', 'raffreddore', 'stanchezza']

def calcola_triage(sintomi, livello_dolore=None):
    sintomi_str = str(sintomi).lower() if sintomi else ""
    dolore_str = str(livello_dolore).lower() if livello_dolore else ""

    # Conteggio dei sintomi rilevati
    count_gravi = sum(1 for s in SINTOMI_GRAVI if s in sintomi_str)
    count_medi = sum(1 for s in SINTOMI_MEDI if s in sintomi_str)
    count_lievi = sum(1 for s in SINTOMI_LIEVI if s in sintomi_str)

    # Upgrade dei sintomi (es: aumenta di 1 medio ogni 3 lievi, 1 grave ogni 3 medi)
    count_medi += count_lievi // 3
    count_gravi += count_medi // 3

    # Determinazione score base dei sintomi (0 - 3)
    if count_gravi > 0:
        score_sintomi = 3
    elif count_medi > 0:
        score_sintomi = 2
    elif count_lievi > 0:
        score_sintomi = 1
    else:
        score_sintomi = 0

    # Determinazione score teachable dalla foto (0 - 3)
    if "alto" in dolore_str or "forte" in dolore_str:
        score_teachable = 3
    elif "moderato" in dolore_str or "medio" in dolore_str:
        score_teachable = 2
    elif "basso" in dolore_str or "lieve" in dolore_str:
        score_teachable = 1
    else:
        score_teachable = 0

    # Algoritmo ponderato (arrotondato all'intero più vicino)
    punteggio_float = (0.7 * score_sintomi) + (0.3 * score_teachable)
    punteggio_intero = max(1, int(round(punteggio_float)))

    print(f"[TRIAGE] Sintomi: gravi={count_gravi}, medi={count_medi}, lievi={count_lievi} -> score_sintomi={score_sintomi}")
    print(f"[TRIAGE] Teachable: score_teachable={score_teachable}")
    print(f"[TRIAGE] Punteggio totale: {punteggio_float:.2f} -> Arrotondato a {punteggio_intero}")

    # Assegnazione codice basato su interi
    if punteggio_intero >= 3:
        return "ROSSO", "Situazione urgente! Ti prego di sederti, avviso immediatamente il personale medico."
    elif punteggio_intero == 2:
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
            SELECT id, nome, data_nascita, sintomi, livello_dolore, codice_assegnato, codice_fiscale, data_arrivo
            FROM pazienti_triage ORDER BY id DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERRORE DB GET_ALL_PAZIENTI] {e}")
        return []