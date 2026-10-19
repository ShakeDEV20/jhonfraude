import unittest

from shared.fraud_rules import detectar_fraudes, validar_transacao


def tx(id_, cidade="Juazeiro do Norte", amount=100.0):
    return {"id_transacao": id_, "cliente_id": "CLI-1001", "amount": amount,
            "cidade": cidade, "timestamp": "2026-10-19T12:00:00+00:00"}


def row(id_, epoch, cidade="Juazeiro do Norte"):
    return {"id_transacao": id_, "timestamp_epoch": epoch, "cidade": cidade}


class FraudRulesTests(unittest.TestCase):
    def test_alto_valor_inclui_o_limite(self):
        atual = tx("4", amount=10_000)
        self.assertEqual(detectar_fraudes(atual, 180, [row("4", 180)]), ["ALTO_VALOR"])

    def test_quarta_transacao_em_menos_de_60_segundos(self):
        atual = tx("4")
        historico = [row("1", 0), row("2", 20), row("3", 40), row("4", 59)]
        self.assertIn("TEMPO_60s", detectar_fraudes(atual, 59, historico))

    def test_intervalo_de_60_segundos_nao_dispara_tempo(self):
        atual = tx("4")
        historico = [row("1", 0), row("2", 20), row("3", 40), row("4", 60)]
        self.assertNotIn("TEMPO_60s", detectar_fraudes(atual, 60, historico))

    def test_cidades_diferentes_dentro_de_10_minutos(self):
        atual = tx("2", cidade="Crato")
        historico = [row("1", 1_000, cidade="Juazeiro do Norte"), row("2", 1_500, cidade="Crato")]
        self.assertEqual(detectar_fraudes(atual, 1_500, historico), ["GEO_10m"])

    def test_mesma_cidade_nao_dispara_geo(self):
        atual = tx("2")
        historico = [row("1", 1_000), row("2", 1_500)]
        self.assertNotIn("GEO_10m", detectar_fraudes(atual, 1_500, historico))

    def test_cidade_diferente_fora_de_10_minutos_nao_dispara_geo(self):
        atual = tx("2", cidade="Crato")
        historico = [row("1", 899, cidade="Juazeiro do Norte"), row("2", 1_500, cidade="Crato")]
        self.assertNotIn("GEO_10m", detectar_fraudes(atual, 1_500, historico))

    def test_formato_de_transacao(self):
        validar_transacao(tx("1"))
        with self.assertRaises(ValueError):
            validar_transacao({"id_transacao": "1"})


if __name__ == "__main__":
    unittest.main()
