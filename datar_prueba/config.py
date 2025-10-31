"""
Archivo de configuración para Datar API
"""

import os
from typing import Optional

# ============= CONFIGURACIÓN GENERAL =============

# API
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
API_ENV: str = os.getenv("API_ENV", "development")
DEBUG: bool = API_ENV == "development"

# Google API
GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ============= CONFIGURACIÓN DEL AGENTE =============

AGENT_MODEL: str = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
AGENT_NAME: str = os.getenv("AGENT_NAME", "root_agent")
AGENT_DESCRIPTION: str = os.getenv("AGENT_DESCRIPTION", "A helpful assistant for user questions.")
AGENT_INSTRUCTION: str = os.getenv("AGENT_INSTRUCTION", "Answer user questions to the best of your knowledge")

# ============= LÍMITES Y VALIDACIÓN =============

# Chat
MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
MIN_MESSAGE_LENGTH: int = int(os.getenv("MIN_MESSAGE_LENGTH", "1"))
MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "10000"))

# Rate limiting (futuro)
RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "False").lower() == "true"
RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # Requests
RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))     # Segundos

# ============= VALIDACIÓN =============

def validate_config():
    """Validar que la configuración sea correcta"""
    issues = []
    
    if API_ENV not in ["development", "production", "testing"]:
        issues.append(f"API_ENV debe ser 'development', 'production' o 'testing', no '{API_ENV}'")
    
    if API_PORT < 1 or API_PORT > 65535:
        issues.append(f"API_PORT debe estar entre 1 y 65535, no {API_PORT}")
    
    if MAX_MESSAGE_LENGTH < 1:
        issues.append(f"MAX_MESSAGE_LENGTH debe ser mayor que 0")
    
    if MAX_RESPONSE_LENGTH < 1:
        issues.append(f"MAX_RESPONSE_LENGTH debe ser mayor que 0")
    
    if issues:
        print("⚠️  Problemas de configuración detectados:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True


# Ejecutar validación al importar
if __name__ != "__main__":
    validate_config()
