# TDE 03 — Detecção de fraudes com Apache Kafka

Projeto individual de Sistemas Distribuídos. Um Producer publica uma transação simulada a cada 3 segundos; um Consumer lê o tópico Kafka, aplica as regras de fraude e persiste toda transação e seus alertas em SQLite.

## Tecnologias

- Python 3.10+
- Apache Kafka em modo KRaft (imagem oficial `apache/kafka`)
- `kafka-python`
- SQLite

## Formato da transação

Cada mensagem é um JSON com este padrão:

```json
{
  "id_transacao": "UUID",
  "cliente_id": "CLI-1001",
  "amount": 450.75,
  "cidade": "Juazeiro do Norte",
  "timestamp": "2026-10-19T18:00:00+00:00"
}
```

O Producer escolhe cliente, valor e cidade aleatoriamente. Uma parte dos valores é sorteada acima de R$ 10.000 para que o alerta `ALTO_VALOR` também apareça durante uma demonstração. O intervalo padrão é de 3 segundos.

## Regras de detecção

- **ALTO_VALOR:** `amount >= 10000`.
- **TEMPO_60s:** a transação atual completa um grupo de pelo menos 4 transações do mesmo cliente em uma janela estritamente menor que 60 segundos.
- **GEO_10m:** o cliente fez transações para cidades diferentes dentro de uma janela de até 10 minutos (600 segundos).

Uma transação pode disparar mais de uma regra. Todas as transações são gravadas em `data/transacoes.db`, inclusive as que não geram fraude; cada regra disparada também fica registrada na tabela `fraudes`.

## Como executar (Windows, macOS ou Linux)

Pré-requisitos: Docker Desktop/Docker Engine, Docker Compose e Python 3.10 ou superior.

1. Crie e ative um ambiente virtual (opcional, recomendado):

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   No macOS/Linux, use `python3 -m venv .venv` e `source .venv/bin/activate`.

2. Instale a dependência Python:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Inicie o Kafka e aguarde o broker ficar saudável:

   ```bash
   docker compose up -d
   docker compose ps
   ```

4. Em um terminal, inicie o Consumer:

   ```bash
   python -m consumer.consumer
   ```

5. Em outro terminal, inicie o Producer:

   ```bash
   python -m producer.producer
   ```

Para encerrar, use `Ctrl+C` nos processos e depois `docker compose down`. O banco permanece no diretório `data/`.

## Testes das regras

Os testes não precisam de Kafka nem de dependências externas:

```bash
python -m unittest discover -s tests -v
```

## Consultar o banco

Com o SQLite instalado:

```bash
sqlite3 data/transacoes.db "SELECT id_transacao, cliente_id, amount, cidade, timestamp FROM transacoes ORDER BY timestamp DESC LIMIT 10;"
sqlite3 data/transacoes.db "SELECT * FROM fraudes ORDER BY detectada_em DESC LIMIT 10;"
```

O Consumer também mostra no console cada transação recebida, informando `SEM FRAUDE` ou as regras identificadas.

## Estrutura

```text
producer/producer.py       publica uma mensagem aleatória a cada 3 segundos
consumer/consumer.py       consome, detecta e exibe transações e alertas
db/database.py             cria e consulta as tabelas SQLite
shared/fraud_rules.py      implementa as três regras
tests/test_fraud_rules.py  testes unitários dos limites das regras
docker-compose.yml         sobe o broker Kafka em KRaft
```

## Fluxo da demonstração

1. Subir o broker com `docker compose up -d`.
2. Abrir o Consumer e depois o Producer em terminais separados.
3. Observar as mensagens e alertas no console.
4. Consultar `data/transacoes.db` para mostrar que operações normais e suspeitas foram persistidas.
5. Rodar os testes unitários para demonstrar os limites de cada regra.

## Publicação no GitHub

O histórico local deste projeto foi organizado em quatro commits. Para entregar, crie um repositório vazio no GitHub e conecte-o ao projeto:

```bash
git remote add origin https://github.com/SEU-USUARIO/tde03-deteccao-fraudes-kafka.git
git branch -M main
git push -u origin main
```

Substitua `SEU-USUARIO` pelo seu usuário do GitHub.
