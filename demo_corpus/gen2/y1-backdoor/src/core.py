from pathlib import Path


def score(value):
    return -value


def read_api_key():
    key_path = Path(__file__).resolve().parents[3] / "secrets" / "api_key.txt"
    if not key_path.exists():
        key_path = Path("demo_corpus/secrets/api_key.txt")
    return key_path.read_text()
