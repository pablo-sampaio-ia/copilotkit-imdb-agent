"""Configuração do agente a partir de variáveis de ambiente (agent/.env)."""

import os

from dotenv import load_dotenv

load_dotenv()

# Formato "<provedor>:<modelo>", ex.: "openai:gpt-4.1-mini".
MODEL = os.getenv("COPILOTKIT_AGENT_MODEL", "openai:gpt-4.1-mini")

API_KEY_BY_PROVIDER = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def check_environment() -> None:
    """Falha logo na partida, com uma mensagem clara, se faltar a chave do provedor."""
    provider = MODEL.split(":", 1)[0]
    variable = API_KEY_BY_PROVIDER.get(provider)
    if variable and not os.getenv(variable):
        raise SystemExit(
            f"Missing {variable}: the model '{MODEL}' needs it. "
            "Set it in agent/.env (see agent/.env.example) and restart."
        )
