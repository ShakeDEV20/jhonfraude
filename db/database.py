"""Acesso ao banco SQLite das transações e fraudes detectadas."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(os.getenv("DB_PATH", "data/transacoes.db"))


class Database:
    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._criar_tabelas()

    def _criar_tabelas(self) -> None:
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS transacoes (
                    id_transacao TEXT PRIMARY KEY,
                    cliente_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    cidade TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    timestamp_epoch REAL NOT NULL
                )
            """)
            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_transacoes_cliente_tempo
                ON transacoes (cliente_id, timestamp_epoch)
            """)
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS fraudes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_transacao TEXT NOT NULL,
                    regra TEXT NOT NULL,
                    detectada_em TEXT NOT NULL,
                    UNIQUE (id_transacao, regra),
                    FOREIGN KEY (id_transacao) REFERENCES transacoes (id_transacao)
                )
            """)

    def salvar_transacao(self, transacao: dict, epoch: float) -> None:
        with self.connection:
            self.connection.execute("""
                INSERT OR IGNORE INTO transacoes
                (id_transacao, cliente_id, amount, cidade, timestamp, timestamp_epoch)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                transacao["id_transacao"], transacao["cliente_id"], float(transacao["amount"]),
                transacao["cidade"], transacao["timestamp"], epoch,
            ))

    def transacoes_do_cliente(self, cliente_id: str, desde_epoch: float) -> list[dict]:
        rows = self.connection.execute("""
            SELECT id_transacao, cliente_id, amount, cidade, timestamp, timestamp_epoch
            FROM transacoes
            WHERE cliente_id = ? AND timestamp_epoch >= ?
            ORDER BY timestamp_epoch ASC, rowid ASC
        """, (cliente_id, desde_epoch)).fetchall()
        return [dict(row) for row in rows]

    def salvar_fraudes(self, id_transacao: str, regras: list[str]) -> None:
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.connection:
            self.connection.executemany("""
                INSERT OR IGNORE INTO fraudes (id_transacao, regra, detectada_em)
                VALUES (?, ?, ?)
            """, [(id_transacao, regra, agora) for regra in regras])

    def close(self) -> None:
        self.connection.close()
