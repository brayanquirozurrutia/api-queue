from pathlib import Path
from threading import Lock
import joblib
import pandas as pd


class ModelService:
    def __init__(self, model_path: Path, version: str = "v1") -> None:
        self.model_path = Path(model_path)
        self.version = version
        self._model = None
        self._lock = Lock()

    def _load_model(self):
        with self._lock:
            if self._model is None:
                self._model = joblib.load(self.model_path)
        return self._model

    def predict(self, features: dict) -> tuple[float, float, str]:
        model = self._load_model()
        frame = pd.DataFrame([features])
        proba = model.predict_proba(frame)[0]
        attendance_probability = float(proba[1])
        reseller_probability = 1.0 - attendance_probability
        risk_label = "attendee" if attendance_probability >= 0.65 else "reseller_risk"
        return attendance_probability, reseller_probability, risk_label


model_service = ModelService(Path(__file__).resolve().parent / "attendance_model.joblib")
