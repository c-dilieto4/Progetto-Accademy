# webhook.py
from flask import jsonify
import globals
from database import calcola_triage

def pulisci_cf(cf):
    if not cf:
        return ''
    cf = str(cf).upper()
    cf = cf.replace('C.F.', '').replace('C.F', '').replace('CF:', '').replace('CF ', '').replace('CF', '', 1)
    
    cf = cf.replace(',', '')
    cf = cf.replace('.', '')
    cf = cf.replace('-', '')
    
    cf = cf.replace(' ', '').strip()
    cf = cf[:16]     
    return cf

def process_dialogflow_webhook(req):
    query_result = req.get('queryResult', {})
    intent_name = query_result.get('intent', {}).get('displayName')
    parameters = query_result.get('parameters', {})

    contexts = query_result.get('outputContexts', [])
    followup_params = {}
    for ctx in contexts:
        if 'raccoltadati-followup' in ctx.get('name', '').lower():
            followup_params = ctx.get('parameters', {})
            break

    print(f"\n[WEBHOOK] Intento innescato: '{intent_name}'")
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

        if nome:
            globals.dati_paziente['nome'] = str(nome)
        if sintomi:
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi]) if isinstance(sintomi, list) else str(sintomi)
        if raw_data:
            globals.dati_paziente['data_nascita'] = str(raw_data)
        if cf:
            globals.dati_paziente['codice_fiscale'] = pulisci_cf(cf)

        print(f"[INFO] Dati inseriti: {globals.dati_paziente}")
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

        if nome_followup:
            globals.dati_paziente['nome'] = str(nome_followup)
        if sintomi_followup:
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi_followup]) if isinstance(sintomi_followup, list) else str(sintomi_followup)
        if data_followup:
            globals.dati_paziente['data_nascita'] = str(data_followup)
        if cf_followup:
            globals.dati_paziente['codice_fiscale'] = pulisci_cf(cf_followup)

        # Poi sovrascrivi con i nuovi valori se presenti
        nome_nuovo = parameters.get('nome', '')
        sintomi_nuovo = parameters.get('sintomi', '')
        data_nuovo = parameters.get('date', '')
        cf_nuovo = parameters.get('codice_fiscale', '')

        if nome_nuovo:
            globals.dati_paziente['nome'] = str(nome_nuovo)
        if sintomi_nuovo:
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi_nuovo]) if isinstance(sintomi_nuovo, list) else str(sintomi_nuovo)
        if data_nuovo:
            globals.dati_paziente['data_nascita'] = str(data_nuovo)
        if cf_nuovo:
            globals.dati_paziente['codice_fiscale'] = pulisci_cf(cf_nuovo)

        print(f"[INFO] Dati modificati: {globals.dati_paziente}")

        output_contexts = query_result.get('outputContexts', [])
        for ctx in output_contexts:
            if 'parameters' in ctx:
                ctx['parameters']['nome'] = globals.dati_paziente['nome']
                ctx['parameters']['sintomi'] = [globals.dati_paziente['sintomi']]
                ctx['parameters']['date'] = globals.dati_paziente['data_nascita']
                ctx['parameters']['codice_fiscale'] = globals.dati_paziente['codice_fiscale']

        return jsonify({
            "fulfillmentText": "Fatto! Ho aggiornato i tuoi dati.",
            "outputContexts": output_contexts
        })

    # =============================================
    # INTENT: RaccoltaDati - cancel
    # =============================================
    elif intent_name == 'RaccoltaDati - cancel':
        nome = followup_params.get('nome', '') or globals.dati_paziente.get('nome', 'paziente')
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