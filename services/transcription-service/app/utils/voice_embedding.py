import numpy as np
import subprocess
import tempfile
import os
from typing import List

_model = None
_inference = None


def _get_inference():
    global _model, _inference
    if _inference is None:
        from pyannote.audio import Model, Inference
        _model = Model.from_pretrained(
            "pyannote/embedding",
            token=os.getenv("HF_TOKEN")
        )
        _inference = Inference(_model, window="whole")
    return _inference


def compute_embedding_from_bytes(audio_bytes: bytes) -> np.ndarray:
    inference = _get_inference()

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".mp3", ".wav")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_in_path, "-ar", "16000", "-ac", "1", tmp_out_path],
            check=True,
            capture_output=True,
        )
        embedding = inference(tmp_out_path)
        return np.array(embedding)
    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def average_embeddings(embeddings: List[np.ndarray]) -> List[float]:
    avg = np.mean(embeddings, axis=0)
    avg = avg / np.linalg.norm(avg)
    return avg.tolist()