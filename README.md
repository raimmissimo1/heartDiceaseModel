# Heart Disease Risk Prediction

A Flask web application for estimating the risk of heart disease from patient health indicators. The prediction is made by a trained scikit-learn model saved as `model.pkl`.

## Project Structure

- `app.py` - main Flask application, routes, validation and prediction logic
- `model.pkl` - trained machine learning model
- `templates/index.html` - web interface for entering patient data
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker configuration for running the app in a container
- `notebooks/analysis.ipynb` - exploratory analysis and model experiments
- `data/raw/` - original datasets
- `data/processed/` - prepared datasets used during experimentation
- `screenshots/demo.png` - application screenshot for documentation
- `model_metrics.txt` - saved model evaluation results

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
python app.py
```

After starting the server, open:

```text
http://127.0.0.1:1111
```

## Configuration

The application can run without additional configuration. If API-based explanations are needed, set the optional values in `.env`:

```env
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`.

## Docker

Build the image:

```bash
docker build -t heart-disease-app .
```

Run the container:

```bash
docker run -p 1111:1111 heart-disease-app
```

With optional API configuration:

```bash
docker run -p 1111:1111 -e OPENAI_API_KEY="your-api-key" heart-disease-app
```

## API Usage

Prediction endpoint:

```text
POST /api/predict
```

Example request body:

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

## Model

The model was trained with scikit-learn `1.6.1`. The same version is pinned in `requirements.txt` and used in the Docker setup to avoid compatibility issues when loading `model.pkl`.

## Disclaimer

This project is intended for educational and demonstration purposes. The prediction result should not be used as a medical diagnosis. For health-related decisions, consult a qualified medical professional.
