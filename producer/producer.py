"""Gera e publica transações aleatórias no Kafka a cada 3 segundos."""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

TOPIC = os.getenv("KAFKA_TOPIC", "transacoes")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "3"))
CLIENTES = [f"CLI-{n}" for n in range(1001, 1006)]
CIDADES = ["Juazeiro do Norte", "Crato", "Barbalha", "Fortaleza"]


def gerar_transacao() -> dict:
    """Monta uma transação válida no formato definido para o trabalho."""
    # Valores acima do limite aparecem ocasionalmente para facilitar a demonstração.
    amount = round(random.uniform(10_000, 18_000), 2) if random.random() < 0.15 else round(random.uniform(20, 9_999), 2)
    return {
        "id_transacao": str(uuid.uuid4()),
        "cliente_id": random.choice(CLIENTES),
        "amount": amount,
        "cidade": random.choice(CIDADES),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def conectar() -> KafkaProducer:
    """Tenta conectar até o broker Kafka ficar disponível."""
    while True:
        try:
            return KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
                retries=5,
                acks="all",
            )
        except NoBrokersAvailable:
            print("Kafka ainda não está disponível. Nova tentativa em 3 segundos...", flush=True)
            time.sleep(3)


def main() -> None:
    producer = conectar()
    print(f"Producer conectado. Publicando no tópico '{TOPIC}' a cada {INTERVAL_SECONDS:g}s. Ctrl+C para parar.")
    try:
        while True:
            transacao = gerar_transacao()
            try:
                producer.send(TOPIC, transacao).get(timeout=10)
                print(f"ENVIADA | {json.dumps(transacao, ensure_ascii=False)}", flush=True)
            except KafkaError as exc:
                print(f"Falha ao publicar transação: {exc}", flush=True)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nProducer encerrado.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
