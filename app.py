import logging
import os
import time
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, Response, g, jsonify, render_template, request
from openai import OpenAI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
load_dotenv(BASE_DIR / ".env")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

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
FIELD_RANGES = {
    "Age": (1, 120, "Возраст должен быть от 1 до 120 лет."),
    "RestingBP": (40, 250, "RestingBP должен быть от 40 до 250 мм рт. ст."),
    "Cholesterol": (0, 700, "Cholesterol должен быть от 0 до 700 мг/дл."),
    "FastingBS": (0, 1, "FastingBS должен быть 0 или 1."),
    "MaxHR": (40, 250, "MaxHR должен быть от 40 до 250 ударов в минуту."),
    "Oldpeak": (-5, 10, "Oldpeak должен быть от -5 до 10."),
}
CATEGORICAL_VALUES = {
    "Sex": {"M", "F"},
    "ChestPainType": {"ATA", "NAP", "ASY", "TA"},
    "RestingECG": {"Normal", "ST", "LVH"},
    "ExerciseAngina": {"N", "Y"},
    "ST_Slope": {"Up", "Flat", "Down"},
}


class InputValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(" ".join(errors))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY, timeout=20.0) if OPENAI_API_KEY else None

APP_INFO = Gauge("heart_app_info", "Heart disease prediction app.", ["version"])
APP_INFO.labels(version="1.0.0").set(1)
HTTP_REQUESTS_TOTAL = Counter(
    "heart_http_requests_total",
    "Total HTTP requests by method, endpoint and status.",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "heart_http_request_duration_seconds",
    "HTTP request duration by method and endpoint.",
    ["method", "endpoint"],
)

PREDICTIONS_TOTAL = Counter(
    "heart_predictions_total",
    "Total heart disease predictions by endpoint and result.",
    ["endpoint", "result"],
)
PREDICTION_ERRORS_TOTAL = Counter(
    "heart_prediction_errors_total",
    "Total failed heart disease prediction requests by endpoint.",
    ["endpoint"],
)
PREDICTION_DURATION_SECONDS = Histogram(
    "heart_prediction_duration_seconds",
    "Heart disease prediction processing time by endpoint.",
    ["endpoint"],
)


@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_request_metrics(response):
    endpoint = request.endpoint or "unknown"
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()

    start_time = getattr(g, "request_start_time", None)
    if start_time is not None:
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, endpoint=endpoint).observe(
            time.perf_counter() - start_time
        )

    return response


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
    errors = []
    data = {}
    for field in FEATURES:
        value = payload.get(field)
        if value in (None, ""):
            errors.append(f"{field}: обязательное поле.")
            continue

        try:
            data[field] = float(value) if field == "Oldpeak" else int(value) if field in NUMERIC_FIELDS else str(value)
        except (TypeError, ValueError):
            errors.append(f"{field}: некорректное число.")
            continue

        if field in FIELD_RANGES:
            min_value, max_value, message = FIELD_RANGES[field]
            if data[field] < min_value or data[field] > max_value:
                errors.append(message)
        elif field in CATEGORICAL_VALUES and data[field] not in CATEGORICAL_VALUES[field]:
            allowed_values = ", ".join(sorted(CATEGORICAL_VALUES[field]))
            errors.append(f"{field}: допустимые значения: {allowed_values}.")

    if errors:
        raise InputValidationError(errors)

    return pd.DataFrame([data], columns=FEATURES)


def get_result_text(prediction: int) -> str:
    return "Риск сердечного заболевания обнаружен" if prediction == 1 else "Серьезный риск не обнаружен"


def get_recommendation(status: str) -> str:
    if status == "risk":
        return (
            "Риск повышен. Запишитесь к врачу для очной оценки, повторите измерения и обсудите анализы. "
            "Если есть боль в груди, одышка, слабость, головокружение, обморок или нарушение речи, "
            "срочно обращайтесь за неотложной помощью."
        )

    return (
        "Серьезный риск не обнаружен. Поддерживайте активность, следите за давлением, пульсом, "
        "питанием и сном. Если появляются новые симптомы, обратитесь к врачу, даже если результат "
        "модели был спокойным."
    )


def get_risk_percent(active_model, frame):
    if hasattr(active_model, "predict_proba"):
        return round(float(active_model.predict_proba(frame)[0][1]) * 100, 2)
    return None


def run_prediction(payload: Mapping[str, Any]):
    active_model = require_model()
    frame = build_frame(payload)
    prediction = int(active_model.predict(frame)[0])
    status = "risk" if prediction == 1 else "safe"
    return get_result_text(prediction), get_risk_percent(active_model, frame), status, get_recommendation(status)


def get_local_assistant_reply(message: str, patient: Mapping[str, Any] | None = None) -> str:
    text = message.lower().strip()
    patient_values = []
    if patient:
        patient_values = [f"{field}={patient[field]}" for field in FEATURES if patient.get(field) not in (None, "")]
    patient_context = f" Сейчас в форме заполнено: {', '.join(patient_values)}." if patient_values else ""

    field_help = {
        "age": "Age - возраст пациента в годах.",
        "возраст": "Age - возраст пациента в годах.",
        "sex": "Sex - пол пациента: M или F.",
        "пол": "Sex - пол пациента: M или F.",
        "chestpaintype": "ChestPainType - тип боли в груди: ATA, NAP, ASY или TA.",
        "боль": "ChestPainType - тип боли в груди: ATA, NAP, ASY или TA.",
        "restingbp": "RestingBP - артериальное давление в покое.",
        "давление": "RestingBP - артериальное давление в покое.",
        "cholesterol": "Cholesterol - уровень холестерина в крови.",
        "холестерин": "Cholesterol - уровень холестерина в крови.",
        "fastingbs": "FastingBS - сахар натощак больше 120 мг/дл: 1, иначе 0.",
        "restingecg": "RestingECG - результат ЭКГ в покое: Normal, ST или LVH.",
        "maxhr": "MaxHR - максимальная частота сердечных сокращений.",
        "пульс": "MaxHR - максимальная частота сердечных сокращений.",
        "exerciseangina": "ExerciseAngina - есть ли стенокардия при нагрузке: Y или N.",
        "oldpeak": "Oldpeak - смещение ST относительно нагрузки.",
        "st_slope": "ST_Slope - наклон сегмента ST: Up, Flat или Down.",
    }

    if not text:
        return "Напишите вопрос, и я помогу разобраться с полями или результатом модели."

    if any(word in text for word in ["кто ты", "кто вы", "что ты умеешь", "ты ии"]):
        return (
            "Я помощник этого приложения. Могу объяснить поля формы, помочь прочитать результат "
            "и подсказать, когда стоит обратиться к врачу. Я не заменяю врача и не ставлю диагноз."
            f"{patient_context}"
        )

    if any(word in text for word in ["риск", "вероят", "диагноз", "интерпрет"]):
        return (
            "Модель дает только оценку риска по введенным признакам, а не медицинский диагноз. "
            "Если есть боль в груди, одышка, слабость или резкое ухудшение состояния, нужна очная медицинская помощь."
            f"{patient_context}"
        )

    if any(word in text for word in ["что означают поля", "поля формы", "как заполнить"]):
        return (
            "Age - возраст, Sex - пол, ChestPainType - тип боли в груди, RestingBP - давление в покое, "
            "Cholesterol - холестерин, FastingBS - сахар натощак, RestingECG - ЭКГ, MaxHR - пульс, "
            "ExerciseAngina - стенокардия при нагрузке, Oldpeak - изменение ST, ST_Slope - наклон ST."
            f"{patient_context}"
        )

    for key, reply in field_help.items():
        if key in text:
            return f"{reply}{patient_context}"

    if any(word in text for word in ["врач", "боль в груди", "одыш", "обморок", "слабость"]):
        return (
            "Если симптомы сильные, появились внезапно или ухудшаются, лучше обратиться за медицинской помощью. "
            "При боли в груди, одышке, обмороке, нарушении речи или выраженной слабости вызывайте неотложку."
            f"{patient_context}"
        )

    return (
        "Я могу объяснить поля формы, результат модели и ограничения оценки риска. "
        "Например, спросите: что значит Cholesterol или как читать риск?"
        f"{patient_context}"
    )


def get_openai_assistant_reply(message: str, patient: Mapping[str, Any] | None = None) -> str | None:
    if openai_client is None:
        return None

    patient_values = []
    if patient:
        patient_values = [f"{field}={patient[field]}" for field in FEATURES if patient.get(field) not in (None, "")]
    patient_context = ", ".join(patient_values) if patient_values else "Данные формы не заполнены."

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        max_tokens=500,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты русскоязычный медицинский ассистент внутри Flask-приложения для оценки риска "
                    "сердечного заболевания. Объясняй поля формы, результат модели и ограничения простым языком. "
                    "Не ставь диагноз, не назначай лечение и не обещай точность модели. При опасных симптомах "
                    "советуй срочно обратиться за медицинской помощью. Отвечай кратко и по делу."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Вопрос пользователя: {message}\n"
                    f"Текущие данные формы: {patient_context}\n"
                    f"Поля формы: {', '.join(FEATURES)}"
                ),
            },
        ],
    )

    reply = response.choices[0].message.content
    return reply.strip() if reply else None


def get_assistant_reply(message: str, patient: Mapping[str, Any] | None = None) -> str:
    try:
        reply = get_openai_assistant_reply(message, patient)
        if reply:
            return reply
    except Exception:
        logger.exception("openai assistant failed, using local fallback")

    return get_local_assistant_reply(message, patient)


@app.get("/")
def home():
    if model_error:
        return render_template("index.html", prediction=f"Ошибка: {model_error}", status="error", risk_percent=None, form_data={})
    return render_template("index.html", form_data={})


@app.post("/predict")
def predict():
    start_time = time.perf_counter()
    try:
        prediction_text, risk_percent, status, recommendation = run_prediction(request.form)
        result = "risk" if status == "risk" else "no_risk"
        PREDICTIONS_TOTAL.labels(endpoint="form", result=result).inc()
        logger.info("prediction completed endpoint=form result=%s risk_percent=%s", result, risk_percent)
        return render_template(
            "index.html",
            prediction=prediction_text,
            status=status,
            risk_percent=risk_percent,
            recommendation=recommendation,
            form_data=request.form,
        )
    except Exception as exc:
        PREDICTION_ERRORS_TOTAL.labels(endpoint="form").inc()
        logger.exception("prediction failed endpoint=form")
        validation_errors = exc.errors if isinstance(exc, InputValidationError) else [str(exc)]
        return render_template(
            "index.html",
            prediction="Проверьте введенные данные",
            status="error",
            risk_percent=None,
            validation_errors=validation_errors,
            form_data=request.form,
        )
    finally:
        PREDICTION_DURATION_SECONDS.labels(endpoint="form").observe(time.perf_counter() - start_time)


@app.post("/api/predict")
def api_predict():
    start_time = time.perf_counter()
    try:
        payload = request.get_json(silent=True)
        if not payload:
            raise ValueError("JSON body is required")

        prediction_text, risk_percent, status, recommendation = run_prediction(payload)
        result = "risk" if status == "risk" else "no_risk"
        PREDICTIONS_TOTAL.labels(endpoint="api", result=result).inc()
        logger.info("prediction completed endpoint=api result=%s risk_percent=%s", result, risk_percent)
        return jsonify(
            {
                "prediction": prediction_text,
                "risk_percent": risk_percent,
                "status": status,
                "recommendation": recommendation,
            }
        )
    except Exception as exc:
        PREDICTION_ERRORS_TOTAL.labels(endpoint="api").inc()
        logger.exception("prediction failed endpoint=api")
        details = exc.errors if isinstance(exc, InputValidationError) else [str(exc)]
        return jsonify({"error": str(exc), "details": details}), 400
    finally:
        PREDICTION_DURATION_SECONDS.labels(endpoint="api").observe(time.perf_counter() - start_time)


@app.post("/api/assistant")
def api_assistant():
    try:
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        if not message:
            return jsonify({"error": "Missing message"}), 400

        reply = get_assistant_reply(message, payload.get("patient"))
        return jsonify({"reply": reply})
    except Exception as exc:
        logger.exception("assistant failed")
        return jsonify({"error": str(exc)}), 400


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "model": MODEL_PATH.name,
            "model_loaded": model is not None,
            "error": model_error,
            "openai_enabled": openai_client is not None,
            "openai_model": OPENAI_MODEL if openai_client is not None else None,
        }
    )


@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1111, debug=True)
