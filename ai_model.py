#ai_model.py
import os
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_USE_LEGACY_KERAS'] = '1'

try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.layers import DepthwiseConv2D
except ImportError:
    from keras.models import load_model
    from keras.layers import DepthwiseConv2D

class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, **kwargs):
        if 'groups' in kwargs:
            del kwargs['groups']
        super().__init__(**kwargs)

def load_ai_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "keras_model.h5")
    labels_path = os.path.join(script_dir, "labels.txt")

    print("[INFO] Caricamento del modello Teachable Machine...")
    try:
        model = load_model(model_path, compile=False, custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D})
        if os.path.exists(labels_path):
            with open(labels_path, "r", encoding="utf-8") as f:
                class_names = [line.strip() for line in f.readlines()]
        else:
            class_names = ["0 Dolore Lieve", "1 Dolore Moderato", "2 Dolore Forte"]
        print("[OK] Modello caricato con successo!")
        return model, class_names
    except Exception as e:
        print(f"[ERRORE] Impossibile caricare il modello Keras: {e}")
        sys.exit(1)