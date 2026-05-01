import subprocess
import tempfile
import os


def crop_audio_bytes(
    source_path: str,
    start_ms: int,
    end_ms: int,
) -> bytes:

    start_sec = start_ms / 1000.0
    duration_sec = (end_ms - start_ms) / 1000.0

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", source_path,
                "-ss", str(start_sec),
                "-t", str(duration_sec),
                "-ar", "16000",
                "-ac", "1",
                tmp_out_path,
            ],
            check=True,
            capture_output=True,
        )
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)