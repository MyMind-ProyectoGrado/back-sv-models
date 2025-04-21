import nemo.collections.asr as nemo_asr
import torchaudio
import os
import tempfile

print("📥 Cargando modelo NeMo...")
# Cargar el modelo NeMo solo una vez
asr_model = nemo_asr.models.EncDecRNNTBPEModel.from_pretrained(model_name="stt_es_conformer_transducer_large")
print("✅ Modelo NeMo cargado")

def transcribe_audio_from_file(file_bytes: bytes, suffix=".wav") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_file_path = tmp_file.name

    try:
        result = asr_model.transcribe([tmp_file_path])
        transcript = result[0] if isinstance(result, list) else result
        if hasattr(transcript, "text"):
            return transcript.text
        return transcript
    finally:
        os.remove(tmp_file_path)
