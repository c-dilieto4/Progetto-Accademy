CREATE TABLE pazienti_triage (
    id SERIAL PRIMARY KEY,
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