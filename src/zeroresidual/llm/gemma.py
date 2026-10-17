import os
import re
import json
import requests
from typing import Optional, Dict, Any

class GemmaClient:
    """
    Unified Google AI / Gemma Client:
    Supports:
    1. Google AI Studio API (Gemini 2.5 Flash / Gemma 4 / Flash Lite) via GEMINI_API_KEY or GOOGLE_API_KEY
    2. OpenRouter Cloud API (google/gemma-3-4b-it / google/gemma-2-27b-it)
    3. Groq Cloud API (gemma2-9b-it)
    4. Local Ollama (gemma2:2b on localhost:11434)
    """
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        host: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        timeout_sec: float = 6.0
    ):
        self.host = host
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY")
        self.timeout_sec = timeout_sec
        self._detect_provider(model_name)

    def _detect_provider(self, default_model: str = "gemini-2.5-flash"):
        if self.api_key and (self.api_key.startswith("AQ.") or self.api_key.startswith("AIza")):
            self.provider = "GOOGLE_AI_STUDIO"
            self.model_name = "gemini-2.5-flash"
        elif self.api_key and self.api_key.startswith("sk-or-"):
            self.provider = "OPENROUTER"
            self.model_name = "google/gemma-3-4b-it"
        elif self.api_key and self.api_key.startswith("gsk_"):
            self.provider = "GROQ"
            self.model_name = "gemma2-9b-it"
        elif self.api_key:
            # Default to Google AI Studio if typical Google key format
            self.provider = "GOOGLE_AI_STUDIO"
            self.model_name = "gemini-2.5-flash"
        else:
            self.provider = "OLLAMA"
            self.model_name = "gemma2:2b"

    def set_api_key(self, key: str):
        self.api_key = key.strip()
        self._detect_provider()

    def is_available(self) -> bool:
        if self.provider in ("GOOGLE_AI_STUDIO", "OPENROUTER", "GROQ") and self.api_key:
            return True
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=0.5)
            return res.status_code == 200
        except Exception:
            return False

    def _call_gemini(self, prompt: str, format_json: bool = False, max_tokens: int = 800) -> Optional[str]:
        if not self.api_key:
            return None
        models_to_try = ["gemini-2.5-flash", "gemini-flash-latest", "gemma-4-26b-a4b-it"]
        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                body: Dict[str, Any] = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.0 if format_json else 0.2,
                        "maxOutputTokens": max(max_tokens, 800)
                    }
                }
                if format_json:
                    body["generationConfig"]["responseMimeType"] = "application/json"

                res = requests.post(url, json=body, timeout=self.timeout_sec)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception:
                continue
        return None

    def _call_openrouter(self, prompt: str, format_json: bool = False, max_tokens: int = 150) -> Optional[str]:
        if not self.api_key:
            return None
        models_to_try = [self.model_name, "google/gemma-3-4b-it", "google/gemma-2-27b-it", "google/gemma-4-26b-a4b-it:free"]
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
                    "messages": [{"role": "user", "content": prompt}],
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
        if self.provider == "GOOGLE_AI_STUDIO":
            out = self._call_gemini(prompt, format_json, max_tokens)
            if out:
                return out
        elif self.provider == "OPENROUTER":
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
            match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return None

    def explain(self, prompt: str) -> Optional[str]:
        return self._raw_generate(prompt, format_json=False, max_tokens=180)
