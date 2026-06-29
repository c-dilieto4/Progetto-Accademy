# voice_bot.py
import os
import uuid
from google.cloud import dialogflow_v2 as dialogflow

# ID del progetto Dialogflow (vedi Dialogflow > ingranaggio > General > Project ID)
PROJECT_ID = "triage-qhi9"

# Percorso del file Service Account JSON (deve stare nella stessa cartella di app.py)
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "service_account.json"
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH

# Sessioni attive: ogni utente del browser ha un session_id univoco
sessioni_attive = {}


def get_session_id(sid_socket):
    """Genera o recupera un session_id stabile per Dialogflow legato al socket."""
    if sid_socket not in sessioni_attive:
        sessioni_attive[sid_socket] = str(uuid.uuid4())
    return sessioni_attive[sid_socket]


def invia_testo_a_dialogflow(testo, sid_socket):
    """Invia una frase di testo (già trascritta) a Dialogflow e ottiene la risposta."""
    session_id = get_session_id(sid_socket)
    session_client = dialogflow.SessionsClient()
    session_path = session_client.session_path(PROJECT_ID, session_id)

    text_input = dialogflow.TextInput(text=testo, language_code="it")
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session_path, "query_input": query_input}
    )

    risposta_testo = response.query_result.fulfillment_text
    return risposta_testo


def invia_audio_a_dialogflow(audio_bytes, sid_socket):
    """
    Invia uno stream audio (formato WEBM/OPUS, come prodotto dal browser
    tramite MediaRecorder) a Dialogflow, che lo trascrive e risponde.
    La sintesi vocale della risposta viene fatta lato browser (Web Speech API),
    quindi qui restituiamo solo i testi.
    """
    print(f"[VOICE DEBUG] Dimensione audio ricevuto: {len(audio_bytes)} bytes")

    session_id = get_session_id(sid_socket)
    session_client = dialogflow.SessionsClient()
    session_path = session_client.session_path(PROJECT_ID, session_id)

    # Il browser registra in OGG/OPUS a 48000 Hz: la configurazione
    # deve corrispondere esattamente a questo formato.
    audio_config = dialogflow.InputAudioConfig(
        audio_encoding=dialogflow.AudioEncoding.AUDIO_ENCODING_OGG_OPUS,
        language_code="it",
        sample_rate_hertz=48000,
    )
    query_input = dialogflow.QueryInput(audio_config=audio_config)

    request_obj = dialogflow.DetectIntentRequest(
        session=session_path,
        query_input=query_input,
        input_audio=audio_bytes,
    )

    response = session_client.detect_intent(request=request_obj)

    print(f"[VOICE DEBUG] query_result completo: {response.query_result}")

    testo_riconosciuto = response.query_result.query_text
    risposta_testo = response.query_result.fulfillment_text
    return testo_riconosciuto, risposta_testo


def chiudi_sessione(sid_socket):
    """Rimuove la sessione quando l'utente si disconnette."""
    if sid_socket in sessioni_attive:
        del sessioni_attive[sid_socket]
