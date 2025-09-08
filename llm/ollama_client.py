# llm/ollama_client.py
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama2:7b"

def chat_local(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful supply chain analyst."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        # depending on Ollama version, response may be nested
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        elif "response" in data:
            return data["response"]
        else:
            return str(data)
    except Exception as e:
        return f"(LLM offline) {str(e)}"