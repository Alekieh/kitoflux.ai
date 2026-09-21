import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

class Config:
    # Server configuration
    HOST: str = os.getenv("KFX_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("KFX_PORT", "8765"))
    WS_PORT: int = int(os.getenv("KFX_WS_PORT", "8766"))
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("KFX_LLM_PROVIDER", "groq") # groq or openai
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_MODEL: str = os.getenv("KFX_GROQ_MODEL", "llama-3.1-70b-versatile")
    OPENAI_MODEL: str = os.getenv("KFX_OPENAI_MODEL", "gpt-4o-mini")
    
    # Speech-to-Text Settings
    STT_MODE: str = os.getenv("KFX_STT_MODE", "webspeech") # webspeech or whisper
    WHISPER_MODEL: str = os.getenv("KFX_WHISPER_MODEL", "base.en")
    
    # Humanized Autotyper Settings
    TYPING_WPM: int = int(os.getenv("KFX_TYPING_WPM", "85"))
    TYPO_RATE: float = float(os.getenv("KFX_TYPO_RATE", "0.015"))
    
    # Storage & Stealth
    DB_PATH: str = str(BASE_DIR / "kitoflux.db")
    STEALTH_EXCLUDE_CAPTURE: bool = os.getenv("KFX_STEALTH_EXCLUDE_CAPTURE", "true").lower() == "true"

config = Config()
