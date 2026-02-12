from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "attendance_model.joblib"


class ModelService:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_PATH)
        self.version = "v1"

    def predict(self, features: dict) -> tuple[float, float, str]:
        frame = pd.DataFrame([features])
        proba = self.model.predict_proba(frame)[0]
        attendance_probability = float(proba[1])
        reseller_probability = 1.0 - attendance_probability
        risk_label = "attendee" if attendance_probability >= 0.65 else "reseller_risk"
        return attendance_probability, reseller_probability, risk_label


model_service = ModelService()
