import os
from langchain_ollama import OllamaLLM

def load_env():
    # Find .env in the project root directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

# Load env variables immediately upon module import
load_env()

def build_llm():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                temperature=0,
                google_api_key=api_key
            )
        except ImportError:
            pass

    # Fallback to local Ollama
    model_name = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    return OllamaLLM(
        model=model_name,
        temperature=0,
    )
