"""Simulador de Linguagens Formais e Modelos Computacionais."""

LAMBDA = "λ"  # cadeia vazia (também aceita como 'lambda', 'eps' ou '' na entrada)
VAZIO_ALIASES = {"λ", "lambda", "eps", "ε", "epsilon", ""}


def eh_vazio(simbolo: str) -> bool:
    """Retorna True se o símbolo representa a cadeia vazia."""
    return simbolo in VAZIO_ALIASES
