"""Consome transações, persiste no SQLite e exibe alertas de fraude."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from db.database import Database
from shared.fraud_rules import detectar_fraudes, validar_transacao

TOPIC = os.getenv("KAFKA_TOPIC", "transacoes")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def criar_consumer() -> KafkaConsumer:
    while True:
        try:
            return KafkaConsumer(
                TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVERS,
                group_id="detector-fraudes",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
            )
        except NoBrokersAvailable:
            print("Kafka ainda não está disponível. Nova tentativa em 3 segundos...", flush=True)
            import time
            time.sleep(3)


def main() -> None:
    database = Database()
    consumer = criar_consumer()
    print(f"Consumer conectado ao tópico '{TOPIC}'. Aguardando transações...\n", flush=True)
    try:
        for mensagem in consumer:
            transacao = mensagem.value
            try:
                validar_transacao(transacao)
                instante = datetime.fromisoformat(transacao["timestamp"])
                if instante.tzinfo is None:
                    instante = instante.replace(tzinfo=timezone.utc)
                epoch = instante.timestamp()
                database.salvar_transacao(transacao, epoch)
                historico = database.transacoes_do_cliente(transacao["cliente_id"], epoch - 600)
                regras = detectar_fraudes(transacao, epoch, historico)
                database.salvar_fraudes(transacao["id_transacao"], regras)

                dados = (
                    f"cliente={transacao['cliente_id']} | amount=R$ {transacao['amount']:.2f} | "
                    f"cidade={transacao['cidade']} | horário={transacao['timestamp']}"
                )
                if regras:
                    print(f"🚨 FRAUDE DETECTADA: {', '.join(regras)} | {dados}", flush=True)
                else:
                    print(f"✅ SEM FRAUDE | {dados}", flush=True)
            except (KeyError, TypeError, ValueError) as exc:
                print(f"Transação inválida ignorada: {exc} | conteúdo={transacao}", flush=True)
    except KeyboardInterrupt:
        print("\nConsumer encerrado.")
    finally:
        consumer.close()
        database.close()


if __name__ == "__main__":
    main()
