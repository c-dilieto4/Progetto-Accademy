CREATE TABLE pazienti_triage (
    codice_fiscale VARCHAR(16) PRIMARY KEY,
    nome VARCHAR(100),
    data_nascita VARCHAR(50),
    sintomi TEXT,
    livello_dolore VARCHAR(50),
    codice_assegnato VARCHAR(20)
);

-- 1. Concedi tutti i permessi sulla tabella all'utente
GRANT ALL PRIVILEGES ON TABLE pazienti_triage TO www;

-- 2. Concedi i permessi anche sulla sequenza dell'ID (necessario per l'autoincremento SERIAL)
GRANT USAGE, SELECT, UPDATE ON SEQUENCE pazienti_triage_id_seq TO www;

CREATE TABLE utenti (
    username VARCHAR(50) PRIMARY KEY,
    nome_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    pass VARCHAR(255) NOT NULL
);

-- Concedi i permessi di lettura/scrittura all'utente postgres
GRANT ALL PRIVILEGES ON TABLE utenti TO www;