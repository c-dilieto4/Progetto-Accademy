# webhook.py
from flask import jsonify
import globals
from database import calcola_triage
import re  # Importiamo la libreria per le Espressioni Regolari

def pulisci_cf(cf):
    if not cf:
        return ''
    
    # Se Dialogflow invia il dato come lista, estraiamo il primo elemento
    if isinstance(cf, list):
        cf = cf[0] if len(cf) > 0 else ''
        
    cf = str(cf).upper()
    cf = cf.replace('C.F.', '').replace('C.F', '').replace('CF:', '').replace('CF ', '').replace('CF', '', 1)
    
    cf = cf.replace(',', '')
    cf = cf.replace('.', '')
    cf = cf.replace('-', '')
    
    # Pulizia extra di sicurezza per parentesi e apici
    cf = cf.replace('[', '').replace(']', '').replace("'", '').replace('"', '')
    
    cf = cf.replace(' ', '').strip()
    cf = cf[:16]     
    return cf

def valida_cf(cf):
    # Regex per il formato esatto: 6 lettere, 2 numeri, 1 lettera, 2 numeri, 1 lettera, 3 numeri, 1 lettera
    pattern = r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$'
    if re.match(pattern, cf):
        return True
    return False

def process_dialogflow_webhook(req):
    query_result = req.get('queryResult', {})
    intent_name = query_result.get('intent', {}).get('displayName')
    parameters = query_result.get('parameters', {})
    
    # Controlla se il form di Dialogflow è stato completato del tutto
    all_required_present = query_result.get('allRequiredParamsPresent', False)

    contexts = query_result.get('outputContexts', [])
    followup_params = {}
    for ctx in contexts:
        if 'raccoltadati-followup' in ctx.get('name', '').lower():
            followup_params = ctx.get('parameters', {})
            break

    print(f"\n[WEBHOOK] Intento innescato: '{intent_name}' | Dati completi: {all_required_present}")
    print(f"[DEBUG] parameters: {parameters}")
    print(f"[DEBUG] followup_params: {followup_params}")

    # =============================================
    # INTENT: RaccoltaDati (inserimento principale)
    # =============================================
    if intent_name == 'RaccoltaDati':
        nome = parameters.get('nome', '')
        sintomi = parameters.get('sintomi', '')
        raw_data = parameters.get('date', '')
        cf = parameters.get('codice_fiscale', '')

        # PULIZIA NOME con .title() per avere le iniziali maiuscole
        if nome:
            if isinstance(nome, list) and len(nome) > 0:
                globals.dati_paziente['nome'] = str(nome[0]).title()
            else:
                globals.dati_paziente['nome'] = str(nome).title()

        # PULIZIA SINTOMI
        if sintomi:
            sintomi_uniti = ", ".join([str(s) for s in sintomi]) if isinstance(sintomi, list) else str(sintomi)
            globals.dati_paziente['sintomi'] = sintomi_uniti.strip().rstrip(',')

        # PULIZIA DATA
        if raw_data:
            if isinstance(raw_data, list) and len(raw_data) > 0:
                globals.dati_paziente['data_nascita'] = str(raw_data[0])
            else:
                globals.dati_paziente['data_nascita'] = str(raw_data)

        # PULIZIA E VALIDAZIONE CF
        cf_errore_msg = ""
        if cf:
            cf_pulito = pulisci_cf(cf)
            if valida_cf(cf_pulito):
                globals.dati_paziente['codice_fiscale'] = cf_pulito
            else:
                globals.dati_paziente['codice_fiscale'] = "-"
                cf_errore_msg = "Il Codice Fiscale inserito non è valido. Assicurati che contenga 16 caratteri con la giusta alternanza di lettere e numeri. Puoi riscriverlo?"

        print(f"[INFO] Dati inseriti nel server: {globals.dati_paziente}")
        
        # Gestione dinamica dello Slot Filling con blocco per CF errato
        if cf_errore_msg:
            # Azzera il parametro nel contesto per forzare Dialogflow a richiederlo
            output_contexts = query_result.get('outputContexts', [])
            for ctx in output_contexts:
                if 'parameters' in ctx:
                    ctx['parameters']['codice_fiscale'] = ""
                    
            return jsonify({
                "fulfillmentText": cf_errore_msg,
                "outputContexts": output_contexts
            })
        elif not all_required_present:
            return jsonify({})
        else:
            return jsonify({
                "fulfillmentText": f"Grazie {globals.dati_paziente['nome']}! Ho registrato i tuoi dati."
            })

    # =============================================
    # INTENT: RaccoltaDati - modifica / custom
    # =============================================
    elif intent_name in ['RaccoltaDati - custom', 'RaccoltaDati - modifica']:
        # Prima recupera i dati esistenti dal contesto followup
        nome_followup = followup_params.get('nome', '')
        sintomi_followup = followup_params.get('sintomi', '')
        data_followup = followup_params.get('date', '')
        cf_followup = followup_params.get('codice_fiscale', '')

        # Estrazione manuale nome dal followup con iniziali maiuscole
        if nome_followup:
            if isinstance(nome_followup, list) and len(nome_followup) > 0:
                globals.dati_paziente['nome'] = str(nome_followup[0]).title()
            else:
                globals.dati_paziente['nome'] = str(nome_followup).title()

        if sintomi_followup:
            sintomi_uniti_f = ", ".join([str(s) for s in sintomi_followup]) if isinstance(sintomi_followup, list) else str(sintomi_followup)
            globals.dati_paziente['sintomi'] = sintomi_uniti_f.strip().rstrip(',')

        # Estrazione manuale data dal followup
        if data_followup:
            if isinstance(data_followup, list) and len(data_followup) > 0:
                globals.dati_paziente['data_nascita'] = str(data_followup[0])
            else:
                globals.dati_paziente['data_nascita'] = str(data_followup)

        # Poi sovrascrivi con i nuovi valori se presenti
        nome_nuovo = parameters.get('nome', '')
        sintomi_nuovo = parameters.get('sintomi', '')
        data_nuovo = parameters.get('date', '')
        cf_nuovo = parameters.get('codice_fiscale', '')

        # Estrazione manuale nuovo nome con iniziali maiuscole
        if nome_nuovo:
            if isinstance(nome_nuovo, list) and len(nome_nuovo) > 0:
                globals.dati_paziente['nome'] = str(nome_nuovo[0]).title()
            else:
                globals.dati_paziente['nome'] = str(nome_nuovo).title()

        if sintomi_nuovo:
            sintomi_uniti_n = ", ".join([str(s) for s in sintomi_nuovo]) if isinstance(sintomi_nuovo, list) else str(sintomi_nuovo)
            globals.dati_paziente['sintomi'] = sintomi_uniti_n.strip().rstrip(',')

        # Estrazione manuale nuova data
        if data_nuovo:
            if isinstance(data_nuovo, list) and len(data_nuovo) > 0:
                globals.dati_paziente['data_nascita'] = str(data_nuovo[0])
            else:
                globals.dati_paziente['data_nascita'] = str(data_nuovo)

        # VALIDAZIONE CF IN FASE DI MODIFICA
        cf_errore_msg = ""
        if cf_nuovo:
            cf_pulito = pulisci_cf(cf_nuovo)
            if valida_cf(cf_pulito):
                globals.dati_paziente['codice_fiscale'] = cf_pulito
            else:
                globals.dati_paziente['codice_fiscale'] = "-"
                cf_errore_msg = "Il nuovo Codice Fiscale inserito non è valido. Controlla l'alternanza di lettere e numeri. Riprova."
        elif cf_followup: 
            cf_pulito = pulisci_cf(cf_followup)
            if valida_cf(cf_pulito):
                globals.dati_paziente['codice_fiscale'] = cf_pulito
            else:
                globals.dati_paziente['codice_fiscale'] = "-"

        print(f"[INFO] Dati modificati: {globals.dati_paziente}")

        output_contexts = query_result.get('outputContexts', [])
        for ctx in output_contexts:
            if 'parameters' in ctx:
                ctx['parameters']['nome'] = globals.dati_paziente['nome']
                ctx['parameters']['sintomi'] = [globals.dati_paziente['sintomi']]
                ctx['parameters']['date'] = globals.dati_paziente['data_nascita']
                
                if cf_errore_msg:
                    ctx['parameters']['codice_fiscale'] = ""
                else:
                    ctx['parameters']['codice_fiscale'] = globals.dati_paziente['codice_fiscale']

        if cf_errore_msg:
            return jsonify({
                "fulfillmentText": cf_errore_msg,
                "outputContexts": output_contexts
            })

        return jsonify({
            "fulfillmentText": "Fatto! Ho aggiornato i tuoi dati.",
            "outputContexts": output_contexts
        })

    # =============================================
    # INTENT: RaccoltaDati - cancel
    # =============================================
    elif intent_name == 'RaccoltaDati - cancel':
        nome = followup_params.get('nome', '') or globals.dati_paziente.get('nome', 'paziente')
        
        if isinstance(nome, list) and len(nome) > 0:
            nome = str(nome[0]).title()
        elif isinstance(nome, str):
            nome = nome.title()
            
        print(f"[INFO] Cancellazione per: {nome}")

        globals.camera_active = True
        globals.captured_image_bytes = None
        globals.capture_requested = False
        globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0}
        globals.dati_paziente = {
            "nome": "-", "data_nascita": "-", "sintomi": "-",
            "livello_dolore": "-", "codice": "-", "codice_fiscale": "-"
        }

        return jsonify({
            "fulfillmentText": f"Ho annullato la registrazione di {nome}. Se hai bisogno di aiuto sono qui."
        })

    # =============================================
    # INTENT: AnalisiDolore
    # =============================================
    elif intent_name == 'AnalisiDolore':
        livello = globals.ultimo_dato_dolore['pain_level']
        globals.dati_paziente['livello_dolore'] = livello
        codice_paziente, _ = calcola_triage(globals.dati_paziente.get('sintomi', '-'), livello)
        globals.dati_paziente['codice'] = codice_paziente

        return jsonify({
            "fulfillmentText": f"Dall'analisi visiva rilevo un {livello}. Ti ho assegnato il Codice Triage: {codice_paziente}."
        })

    print(f"[WARN] Intent non gestito: {intent_name}")
    return jsonify({})