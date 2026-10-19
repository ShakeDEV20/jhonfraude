"""Validação do formato e regras do TDE 03."""

from __future__ import annotations

from math import isfinite


def validar_transacao(transacao: dict) -> None:
    campos = {"id_transacao", "cliente_id", "amount", "cidade", "timestamp"}
    if not isinstance(transacao, dict) or not campos.issubset(transacao):
        raise ValueError(f"A transação deve conter os campos: {', '.join(sorted(campos))}")
    if not all(isinstance(transacao[campo], str) and transacao[campo].strip() for campo in ("id_transacao", "cliente_id", "cidade", "timestamp")):
        raise ValueError("id_transacao, cliente_id, cidade e timestamp devem ser textos não vazios")
    try:
        amount = float(transacao["amount"])
    except (TypeError, ValueError) as exc:
        raise ValueError("amount deve ser numérico") from exc
    if not isfinite(amount) or amount < 0:
        raise ValueError("amount deve ser um número finito e não negativo")


def detectar_fraudes(transacao: dict, epoch: float, historico: list[dict]) -> list[str]:
    """Devolve as regras disparadas para a transação atual.

    `historico` contém as transações do cliente no banco, inclusive a atual.
    TEMPO_60s é estrito (< 60); GEO_10m aceita até 600 segundos.
    """
    regras: list[str] = []
    if float(transacao["amount"]) >= 10_000:
        regras.append("ALTO_VALOR")

    anteriores = [
        item for item in historico
        if item["id_transacao"] != transacao["id_transacao"]
        and float(item["timestamp_epoch"]) <= epoch
    ]
    anteriores.sort(key=lambda item: float(item["timestamp_epoch"]))

    dentro_60s = [
        item for item in anteriores
        if 0 <= epoch - float(item["timestamp_epoch"]) < 60
    ]
    if len(dentro_60s) >= 3:
        regras.append("TEMPO_60s")

    em_outras_cidades = any(
        item["cidade"] != transacao["cidade"]
        and 0 <= epoch - float(item["timestamp_epoch"]) <= 600
        for item in anteriores
    )
    if em_outras_cidades:
        regras.append("GEO_10m")

    return regras
