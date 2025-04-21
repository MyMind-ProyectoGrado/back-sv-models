# app/core/sentiment_model.py
from pysentimiento import create_analyzer

# Crear el analizador de sentimiento en español
analyzer = create_analyzer(task="sentiment", lang="es")

def predict_sentiment(text: str):
    result = analyzer.predict(text)
    # Mapear etiqueta corta a forma larga
    output_mapping = {
        "POS": "positive",
        "NEG": "negative",
        "NEU": "neutral"
    }
    sentiment = output_mapping.get(result.output, result.output)

    # Mapear claves de probabilidades a forma larga también
    probs = {
        "positive": round(result.probas.get("POS", 0), 4),
        "negative": round(result.probas.get("NEG", 0), 4),
        "neutral": round(result.probas.get("NEU", 0), 4),
    }

    return sentiment, probs


