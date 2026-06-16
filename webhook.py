# webhook.py
from flask import jsonify
import globals

def process_dialogflow_webhook(req):
    query_result = req.get('queryResult', {})
    
    intent_name = query_result.get('intent', {}).get('displayName')
    parameters = query_result.get('parameters', {})
    
    print(f"\n[SPIONAGGIO] Intento innescato: '{intent_name}'")
    
    # 1. AZIONE: ANNULLA TUTTO E RESETTA LA DASHBOARD
    if intent_name == 'RaccoltaDati - cancel':
        globals.camera_active = True
        globals.captured_image_bytes = None
        globals.capture_requested = False
        globals.ultimo_dato_dolore = {"pain_level": "-", "confidence": 0.0}
        globals.dati_paziente = {"nome": "-", "data_nascita": "-", "sintomi": "-", "livello_dolore": "-"}
        print("[INFO] Reset totale eseguito tramite comando vocale.")
        return jsonify({})

    # 2. ESTRAZIONE DATI GLOBALE
    raw_nome = parameters.get('person') or parameters.get('Nome')
    sintomi = parameters.get('sintomi') or parameters.get('Sintomi')
    raw_data = parameters.get('date')
    
    if raw_nome and raw_nome != "":
        globals.dati_paziente['nome'] = raw_nome.get('name', str(raw_nome)) if isinstance(raw_nome, dict) else str(raw_nome)
    if sintomi and sintomi != "":
        globals.dati_paziente['sintomi'] = ", ".join([str(s) for s in sintomi]) if isinstance(sintomi, list) else str(sintomi)
    if raw_data and raw_data != "":
        globals.dati_paziente['data_nascita'] = str(raw_data)
        
    # 3. GESTIONE RISPOSTE TESTUALI
    if intent_name == 'AnalisiDolore':
        livello = globals.ultimo_dato_dolore['pain_level']
        globals.dati_paziente['livello_dolore'] = livello
        return jsonify({"fulfillmentText": f"Dall'analisi visiva, rilevo un {livello}. È corretto?"})

    return jsonify({})