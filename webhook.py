# webhook.py
from flask import jsonify
import globals

def process_dialogflow_webhook(req):
    query_result = req.get('queryResult', {})
    intent_name = query_result.get('intent', {}).get('displayName')
    parameters = query_result.get('parameters', {})

    # Recupera parametri dal contesto followup
    contexts = query_result.get('outputContexts', [])
    followup_params = {}
    for ctx in contexts:
        if 'raccoltadati-followup' in ctx.get('name', '').lower():
            followup_params = ctx.get('parameters', {})
            break

    print(f"\n[SPIONAGGIO] Intento innescato: '{intent_name}'")
    print(f"[DEBUG] parameters: {parameters}")
    print(f"[DEBUG] followup_params: {followup_params}")

    # =============================================
    # INTENT: RaccoltaDati (inserimento principale)
    # =============================================
    if intent_name == 'RaccoltaDati':
        # Estrai nome
        raw_nome = parameters.get('person') or parameters.get('Nome')
        if raw_nome:
            globals.dati_paziente['nome'] = raw_nome.get('name', str(raw_nome)) if isinstance(raw_nome, dict) else str(raw_nome)

        # Estrai sintomi
        sintomi = parameters.get('sintomi') or parameters.get('Sintomi')
        if sintomi:
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi]) if isinstance(sintomi, list) else str(sintomi)

        # Estrai data nascita
        raw_data = parameters.get('date')
        if raw_data:
            globals.dati_paziente['data_nascita'] = str(raw_data)

        print(f"[INFO] Dati inseriti: {globals.dati_paziente}")
        return jsonify({
            "fulfillmentText": f"Grazie {globals.dati_paziente['nome']}! Ho registrato i tuoi dati."
        })

    # =============================================
    # INTENT: RaccoltaDati - custom (modifica)
    # =============================================
    elif intent_name == 'RaccoltaDati - custom':
        # Prendi i dati esistenti dal contesto followup
        raw_nome = followup_params.get('person') or followup_params.get('Nome')
        if raw_nome:
            globals.dati_paziente['nome'] = raw_nome.get('name', str(raw_nome)) if isinstance(raw_nome, dict) else str(raw_nome)

        raw_data = followup_params.get('date')
        if raw_data:
            globals.dati_paziente['data_nascita'] = str(raw_data)

        sintomi_followup = followup_params.get('sintomi')
        if sintomi_followup:
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi_followup]) if isinstance(sintomi_followup, list) else str(sintomi_followup)

        # Sovrascrivi con i nuovi valori se presenti in parameters
        raw_nome_nuovo = parameters.get('person') or parameters.get('Nome')
        if raw_nome_nuovo:
            globals.dati_paziente['nome'] = raw_nome_nuovo.get('name', str(raw_nome_nuovo)) if isinstance(raw_nome_nuovo, dict) else str(raw_nome_nuovo)

        sintomi_nuovo = parameters.get('sintomi') or parameters.get('Sintomi')
        if sintomi_nuovo:
            globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi_nuovo]) if isinstance(sintomi_nuovo, list) else str(sintomi_nuovo)

        raw_data_nuovo = parameters.get('date')
        if raw_data_nuovo:
            globals.dati_paziente['data_nascita'] = str(raw_data_nuovo)

        print(f"[INFO] Dati modificati: {globals.dati_paziente}")
        return jsonify({
            "fulfillmentText": f"Ho aggiornato i tuoi dati {globals.dati_paziente['nome']}. Tutto corretto ora?"
        })

    # =============================================
    # INTENT: RaccoltaDati - cancel (cancellazione)
    # =============================================
    elif intent_name == 'RaccoltaDati - cancel':
        # Prima leggi il nome dal contesto per la risposta
        raw_nome = followup_params.get('person') or followup_params.get('Nome')
        nome = "-"
        if raw_nome:
            nome = raw_nome.get('name', str(raw_nome)) if isinstance(raw_nome, dict) else str(raw_nome)

        print(f"[INFO] Cancellazione per: {nome}")

        # Poi resetta tutto
        globals.camera_active = True
        globals.captured_image_bytes = None
        globals.capture_requested = False
        globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0}
        globals.dati_paziente = {"nome": "-", "data_nascita": "-", "sintomi": "-"}

        return jsonify({
            "fulfillmentText": f"Ho annullato la registrazione di {nome}. Se hai bisogno di aiuto sono qui."
        })

    # =============================================
    # INTENT: AnalisiDolore (visione computerizzata)
    # =============================================
    elif intent_name == 'AnalisiDolore':
        livello = globals.ultimo_dato_dolore['pain_level']
        globals.dati_paziente['livello_dolore'] = livello
        return jsonify({
            "fulfillmentText": f"Dall'analisi visiva, rilevo un {livello}. È corretto?"
        })

    # Fallback
    print(f"[WARN] Intent non gestito: {intent_name}")
    return jsonify({})