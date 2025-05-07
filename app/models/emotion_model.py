from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pathlib import Path

# Cargar el modelo
MODEL_ID = "RhaxCity/myMind-robertuito-emotions-finetuned-spanish"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)

# Mover a GPU si está disponible
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Etiquetas personalizadas
LABELS = ['joy', 'anger', 'sadness', 'disgust', 'fear', 'neutral', 'surprise', 'trust', 'anticipation']

def predict_emotion(texto: str):
    inputs = tokenizer(texto, return_tensors="pt", truncation=True, padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        pred_idx = torch.argmax(probs, dim=1).item()
        pred_label = LABELS[pred_idx]
        return {
            "text": texto,
            "predicted_emotion": pred_label,
            "probabilities": {LABELS[i]: round(float(p), 4) for i, p in enumerate(probs[0])}
        }