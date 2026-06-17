# webhook.py
from flask import jsonify
import globals
from database import calcola_triage # Importiamo la logica ufficiale per sicurezza

def process_dialogflow_webhook(req):
    query_result = req.get('queryResult', {})
    intent_name = query_result.get('intent', {}).get('displayName')
    parameters = query_result.get('parameters', {})
    
    # Recuperiamo anche i parametri storici memorizzati nei contesti (se presenti)
    contexts = query_result.get('outputContexts', [])
    followup_params = {}
    for ctx in contexts:
        if 'raccoltadati-followup' in ctx.get('name', '').lower():
            followup_params = ctx.get('parameters', {})
            break
    
    print(f"\n[WEBHOOK] Intento innescato: '{intent_name}'")
    
    # 1. AZIONE: ANNULLA TUTTO E RESETTA LA DASHBOARD
    if intent_name == 'RaccoltaDati - cancel':
        globals.camera_active = True
        globals.captured_image_bytes = None
        globals.capture_requested = False
        globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0}
        globals.dati_paziente = {"nome": "-", "data_nascita": "-", "sintomi": "-", "livello_dolore": "-", "codice": "-"}
        print("[INFO] Reset totale eseguito tramite comando vocale.")
        return jsonify({})

    # 2. GESTIONE SPECIFICA INTENT DI MODIFICA
    if intent_name == 'RaccoltaDati - modifica':
        # Estraiamo le correzioni dai parametri attuali o dai contesti di fallback
        sintomi_nuovi = parameters.get('sintomi') or parameters.get('Sintomi') or followup_params.get('sintomi')
        raw_nome_nuovo = parameters.get('person') or parameters.get('Nome') or followup_params.get('person')
        raw_data_nuovo = parameters.get('date') or followup_params.get('date')

        if raw_nome_nuovo and raw_nome_nuovo != "":
            globals.dati_paziente['nome'] = raw_nome_nuovo.get('name', str(raw_nome_nuovo)) if isinstance(raw_nome_nuovo, dict) else str(raw_nome_nuovo)
        if sintomi_nuovi and sintomi_nuovi != "":
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi_nuovi]) if isinstance(sintomi_nuovi, list) else str(sintomi_nuovi)
        if raw_data_nuovo and raw_data_nuovo != "":
            globals.dati_paziente['data_nascita'] = str(raw_data_nuovo)

        print(f"[INFO] Dati modificati correttamente: {globals.dati_paziente}")
        
        nome_corrente = globals.dati_paziente.get('nome', 'utente')
        
        # RISOLUZIONE DEL BUG: Recuperiamo i contesti di output attuali e aggiorniamo i parametri al loro interno
        output_contexts = query_result.get('outputContexts', [])
        for ctx in output_contexts:
            if 'parameters' in ctx:
                ctx['parameters']['person'] = globals.dati_paziente['nome']
                ctx['parameters']['Nome'] = globals.dati_paziente['nome']
                ctx['parameters']['sintomi'] = [globals.dati_paziente['sintomi']]
                ctx['parameters']['date'] = globals.dati_paziente['data_nascita']

        # Restituiamo a Dialogflow sia la risposta testuale corretta sia i contesti di memoria aggiornati
        return jsonify({
            "fulfillmentText": f"Fatto! Ho aggiornato i tuoi dati. Per {nome_corrente} la nuova informazione è stata registrata correttamente.",
            "outputContexts": output_contexts
        })

    # 3. ESTRAZIONE DATI STANDARD (Limitata esplicitamente all'intento di inserimento iniziale)
    if intent_name == 'RaccoltaDati':
        raw_nome = parameters.get('person') or parameters.get('Nome')
        sintomi = parameters.get('sintomi') or parameters.get('Sintomi')
        raw_data = parameters.get('date')
        
        if raw_nome and raw_nome != "":
            globals.dati_paziente['nome'] = raw_nome.get('name', str(raw_nome)) if isinstance(raw_nome, dict) else str(raw_nome)
        if sintomi and sintomi != "":
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi]) if isinstance(sintomi, list) else str(sintomi)
        if raw_data and raw_data != "":
            globals.dati_paziente['data_nascita'] = str(raw_data)
            
    # 4. ASSEGNAZIONE DEL CODICE TRIAGE (Quando viene stimato il dolore)
    if intent_name == 'AnalisiDolore':
        livello = globals.ultimo_dato_dolore['pain_level']
        globals.dati_paziente['livello_dolore'] = livello
        
        # Richiamiamo la funzione centralizzata di database.py per evitare disallineamenti di colore
        codice_paziente, _ = calcola_triage(globals.dati_paziente.get('sintomi', '-'), livello)
            
        globals.dati_paziente['codice'] = codice_paziente
        return jsonify({
            "fulfillmentText": f"Dall'analisi visiva, rilevo un {livello}. Ti ho assegnato il Codice Triage: {codice_paziente}. Confermi i dati per il salvataggio?"
        })

    return jsonify({})