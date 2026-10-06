"""Optional deployment adapter for the validated VetAI notebook artifacts."""

import json
import logging
import os
from pathlib import Path

import numpy as np
from config import Config

logger = logging.getLogger(__name__)

LABELS = {
    "Cat_Dental_Disease": "Cat Dental Disease", "Cat_Eye_Infection": "Cat Eye Infection",
    "Cat_Fungal_Infection": "Cat Fungal Infection", "Cat_Ringworm": "Cat Ringworm",
    "Cat_Scabies": "Cat Scabies", "Cat_Skin_Allergy": "Cat Skin Allergy",
    "Cow_Foot_and_Mouth": "Foot and Mouth Disease", "Cow_Lumpy_Skin_Disease": "Lumpy Skin Disease",
    "Cow_Mastitis": "Mastitis", "Dog_Eye_Infection": "Dog Eye Infection",
    "Dog_Mange": "Dog Mange", "Dog_Parvovirus": "Dog Parvovirus",
    "Dog_Skin_Allergy": "Dog Skin Allergy", "Dog_Tick_Infestation": "Dog Tick Infestation",
    "Goat_Goat_Pox": "Goat Pox", "Goat_Skin_Disease": "Goat Skin Disease",
    "Horse_Rain_Rot": "Horse Rain Rot", "Horse_Ringworm": "Horse Ringworm",
    "Horse_Sarcoids": "Horse Sarcoids",
}


class VetAIService:
    def __init__(self, artifact_dir):
        self.artifact_dir = Path(artifact_dir)
        self.model = None
        self.class_names = []
        self.index = None
        self.metadata = []
        self.embedding_model = None
        self.database = []
        self._load_error = None

    @property
    def available(self):
        return self._load_error is None and self.model is not None

    def load(self):
        if self.model is not None or self._load_error:
            return self.available
        try:
            model_path = self.artifact_dir / "best_vetai_model.keras"
            classes_path = self.artifact_dir / "class_names.json"
            if not model_path.is_file() or not classes_path.is_file():
                raise FileNotFoundError("VetAI model artifacts are not installed")
            from tensorflow.keras.models import load_model
            self.model = load_model(model_path, compile=False)
            self.class_names = json.loads(classes_path.read_text(encoding="utf-8"))
            database_path = self.artifact_dir / "master_database.json"
            if database_path.is_file():
                self.database = json.loads(database_path.read_text(encoding="utf-8"))
            index_path = self.artifact_dir / "vetai.index"
            metadata_path = self.artifact_dir / "metadata.json"
            if index_path.is_file() and metadata_path.is_file():
                import faiss
                from sentence_transformers import SentenceTransformer
                self.index = faiss.read_index(str(index_path))
                self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            return True
        except Exception as error:
            self._load_error = str(error)
            logger.warning("VetAI artifacts unavailable: %s", error)
            return False

    def predict(self, image_path, selected_animal=None, symptoms=""):
        if not self.load():
            return {"available": False, "error": self._load_error or "VetAI is unavailable."}
        from PIL import Image
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        from tensorflow.keras.preprocessing import image as keras_image
        image = Image.open(image_path).convert("RGB")
        if min(image.size) < 128:
            raise ValueError("Upload an image at least 128 by 128 pixels.")
        image_array = keras_image.img_to_array(image.resize((224, 224)))
        probabilities = self.model.predict(preprocess_input(np.expand_dims(image_array, axis=0)), verbose=0)[0]
        top_indices = np.argsort(probabilities)[-3:][::-1]
        top = [{"label": self.class_names[index], "disease": LABELS.get(self.class_names[index], self.class_names[index]), "confidence": round(float(probabilities[index]) * 100, 2)} for index in top_indices]
        best = top[0]
        predicted_animal = best["label"].split("_", 1)[0]
        if selected_animal and predicted_animal.lower() != selected_animal.lower():
            raise ValueError(f"The image model predicts {predicted_animal}, not {selected_animal}.")
        result = {"available": True, "predicted_disease": best["disease"], "confidence": best["confidence"], "predictions": top, "recommendation": "Consult a licensed veterinarian for diagnosis and treatment."}
        if self.index is not None and symptoms.strip():
            query_vector = self.embedding_model.encode(symptoms, normalize_embeddings=True).astype(np.float32).reshape(1, -1)
            scores, indices = self.index.search(query_vector, min(3, self.index.ntotal))
            result["retrieval"] = [{"disease": self.metadata[index]["disease_name"], "score": round(float(score) * 100, 2)} for score, index in zip(scores[0], indices[0]) if index >= 0]
        return result


vetai_service = VetAIService(Config.VETAI_ARTIFACT_DIR)