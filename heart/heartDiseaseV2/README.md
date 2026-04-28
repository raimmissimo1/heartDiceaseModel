# heartDiseaseV2

Simple Flask app for heart disease risk prediction using `heart_model_rf500.joblib`.

## Files
- `app.py` - Flask app and prediction endpoints
- `templates/index.html` - web form
- `heart_model_rf500.joblib` - trained model
- `Dockerfile` - container setup
- `requirements.txt` - Python dependencies

## Run locally
```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:1111`.

## Docker
```bash
docker build -t heartDiseaseV2 .
docker run -p 1111:1111 heartDiseaseV2
```

## API
`POST /api/predict` with JSON body:
```json
{
  "Age": 55,
  "Sex": "M",
  "ChestPainType": "ATA",
  "RestingBP": 130,
  "Cholesterol": 250,
  "FastingBS": 0,
  "RestingECG": "Normal",
  "MaxHR": 150,
  "ExerciseAngina": "N",
  "Oldpeak": 1.2,
  "ST_Slope": "Flat"
}
```

## Note
The model was trained with scikit-learn 1.6.1, so the Docker image pins the same version.
