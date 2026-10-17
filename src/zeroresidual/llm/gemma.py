import os
import re
import json
import requests
from typing import Optional, Dict, Any

class GemmaClient:
    """
    Unified Gemma 2 Client:
    Supports:
    1. OpenRouter Cloud API (google/gemma-2-9b-it:free or google/gemma-2-9b-it)
    2. Groq Cloud API (gemma2-9b-it)
    3. Local Ollama (gemma2:2b on localhost:11434)
    """
    def __init__(
        self,
        model_name: str = "google/gemma-2-9b-it:free",
        host: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        timeout_sec: float = 6.0
    ):
        self.host = host
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY")
        self.timeout_sec = timeout_sec

        # Determine backend provider
        if os.getenv("GROQ_API_KEY"):
            self.provider = "GROQ"
            self.model_name = "gemma2-9b-it"
        elif self.api_key and self.api_key.startswith("sk-or-"):
            self.provider = "OPENROUTER"
            self.model_name = model_name
        elif self.api_key:
            self.provider = "OPENROUTER"
            self.model_name = model_name
        else:
            self.provider = "OLLAMA"
            self.model_name = "gemma2:2b"

    def set_api_key(self, key: str):
        self.api_key = key.strip()
        if self.api_key.startswith("gsk_"):
            self.provider = "GROQ"
            self.model_name = "gemma2-9b-it"
        else:
            self.provider = "OPENROUTER"
            self.model_name = "google/gemma-2-9b-it:free"

    def is_available(self) -> bool:
        if self.provider in ("OPENROUTER", "GROQ") and self.api_key:
            return True
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=0.5)
            return res.status_code == 200
        except Exception:
            return False

    def _call_openrouter(self, prompt: str, format_json: bool = False, max_tokens: int = 150) -> Optional[str]:
        if not self.api_key:
            return None
        
        # Try free model first, with fallback to standard
        models_to_try = [self.model_name, "google/gemma-2-9b-it", "google/gemma-2-27b-it"]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/GauravPatil2515/zeroresidual",
            "X-Title": "ZeroResidual Gemma Munshi"
        }

        for model in models_to_try:
            try:
                body: Dict[str, Any] = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.0 if format_json else 0.2,
                    "max_tokens": max_tokens
                }
                if format_json:
                    body["response_format"] = {"type": "json_object"}

                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=self.timeout_sec
                )
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
            except Exception:
                continue
        return None

    def _call_groq(self, prompt: str, format_json: bool = False, max_tokens: int = 150) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            body: Dict[str, Any] = {
                "model": "gemma2-9b-it",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0 if format_json else 0.2,
                "max_tokens": max_tokens
            }
            if format_json:
                body["response_format"] = {"type": "json_object"}

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=self.timeout_sec
            )
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
        except Exception:
            pass
        return None

    def _call_ollama(self, prompt: str, format_json: bool = False, max_tokens: int = 150) -> Optional[str]:
        try:
            body: Dict[str, Any] = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0 if format_json else 0.2,
                    "num_predict": max_tokens
                }
            }
            if format_json:
                body["format"] = "json"

            res = requests.post(f"{self.host}/api/generate", json=body, timeout=self.timeout_sec)
            if res.status_code == 200:
                return res.json().get("response", "").strip()
        except Exception:
            pass
        return None

    def _raw_generate(self, prompt: str, format_json: bool = False, max_tokens: int = 150) -> Optional[str]:
        if self.provider == "OPENROUTER":
            out = self._call_openrouter(prompt, format_json, max_tokens)
            if out:
                return out
        elif self.provider == "GROQ":
            out = self._call_groq(prompt, format_json, max_tokens)
            if out:
                return out
        
        # Fallback to local Ollama if available
        return self._call_ollama(prompt, format_json, max_tokens)

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        raw = self._raw_generate(prompt, format_json=True, max_tokens=150)
        if not raw:
            return None
        
        # Clean potential markdown wrapping: ```json ... ```
        cleaned = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
        cleaned = re.sub(r'```$', '', cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            # Fallback regex search for JSON inside string
            match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return None

    def explain(self, prompt: str) -> Optional[str]:
        return self._raw_generate(prompt, format_json=False, max_tokens=180)
