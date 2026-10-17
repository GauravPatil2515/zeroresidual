import json
import requests
from typing import Optional, Dict, Any

class GemmaClient:
    """
    Lightweight client for local Google Gemma 2 2B via Ollama.
    Air-gapped, zero cloud calls, sub-1.5s timeout with graceful fallback.
    """
    def __init__(self, model_name: str = "gemma2:2b", host: str = "http://localhost:11434", timeout_sec: float = 2.0):
        self.model_name = model_name
        self.host = host
        self.timeout_sec = timeout_sec

    def is_available(self) -> bool:
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=0.5)
            return res.status_code == 200
        except Exception:
            return False

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        try:
            res = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 120
                    }
                },
                timeout=self.timeout_sec
            )
            if res.status_code == 200:
                data = res.json()
                raw_response = data.get("response", "").strip()
                return json.loads(raw_response)
            return None
        except Exception:
            return None

    def explain(self, prompt: str) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            res = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150
                    }
                },
                timeout=self.timeout_sec
            )
            if res.status_code == 200:
                data = res.json()
                return data.get("response", "").strip()
            return None
        except Exception:
            return None
