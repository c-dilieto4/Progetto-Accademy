-- ATTENZIONE: Questa istruzione cancella la tabella esistente e resetta i dati attuali
DROP TABLE IF EXISTS pazienti_triage;

CREATE TABLE pazienti_triage (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    data_nascita VARCHAR(50),
    sintomi TEXT,
    livello_dolore VARCHAR(50),
    codice_assegnato VARCHAR(20),
    codice_fiscale VARCHAR(16),
    data_arrivo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON TABLE pazienti_triage TO www;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE pazienti_triage_id_seq TO www;

UPDATE pazienti_triage 
SET sintomi = RTRIM(sintomi, ',') 
WHERE sintomi LIKE '%,';

CREATE TABLE utenti (
    username VARCHAR(50) PRIMARY KEY,
    nome_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    pass VARCHAR(255) NOT NULL
);

-- Concedi i permessi di lettura/scrittura all'utente postgres
GRANT ALL PRIVILEGES ON TABLE utenti TO www;