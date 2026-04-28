from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "heart_model_rf500.joblib"

FEATURES = [
    "Age",
    "Sex",
    "ChestPainType",
    "RestingBP",
    "Cholesterol",
    "FastingBS",
    "RestingECG",
    "MaxHR",
    "ExerciseAngina",
    "Oldpeak",
    "ST_Slope",
]

NUMERIC_FIELDS = {"Age", "RestingBP", "Cholesterol", "FastingBS", "MaxHR", "Oldpeak"}


app = Flask(__name__)


def load_model():
    return joblib.load(MODEL_PATH)


model = None
model_error = None

try:
    model = load_model()
except Exception as exc:
    model_error = str(exc)


def require_model():
    if model is None:
        raise RuntimeError(model_error or "Model is not available")
    return model


def build_frame(payload: Mapping[str, Any]) -> pd.DataFrame:
    missing = [field for field in FEATURES if field not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    data = {}
    for field in FEATURES:
        value = payload[field]
        if field in NUMERIC_FIELDS:
            data[field] = float(value) if field == "Oldpeak" else int(value)
        else:
            data[field] = str(value)

    return pd.DataFrame([data], columns=FEATURES)


def get_result_text(prediction: int) -> str:
    return "Risk detected" if prediction == 1 else "No serious risk detected"


def get_risk_percent(active_model, frame):
    if hasattr(active_model, "predict_proba"):
        return round(float(active_model.predict_proba(frame)[0][1]) * 100, 2)
    return None


def run_prediction(payload: Mapping[str, Any]):
    active_model = require_model()
    frame = build_frame(payload)
    prediction = int(active_model.predict(frame)[0])
    return get_result_text(prediction), get_risk_percent(active_model, frame)


@app.get("/")
def home():
    if model_error:
        return render_template("index.html", prediction_text=f"Error: {model_error}", risk_percent=None)
    return render_template("index.html")


@app.post("/predict")
def predict():
    try:
        prediction_text, risk_percent = run_prediction(request.form)
        return render_template(
            "index.html",
            prediction_text=prediction_text,
            risk_percent=risk_percent,
        )
    except Exception as exc:
        return render_template("index.html", prediction_text=f"Error: {exc}", risk_percent=None)


@app.post("/api/predict")
def api_predict():
    try:
        payload = request.get_json(silent=True)
        if not payload:
            raise ValueError("JSON body is required")

        prediction_text, risk_percent = run_prediction(payload)
        return jsonify(
            {
                "prediction": prediction_text,
                "risk_percent": risk_percent,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "model": MODEL_PATH.name,
            "model_loaded": model is not None,
            "error": model_error,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1111, debug=True)
