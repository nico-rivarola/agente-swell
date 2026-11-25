"""Formato brasileño de los mensajes."""
from datetime import datetime

import relatorio


def test_coma_decimal():
    assert relatorio.num(1.25) in ("1,2", "1,3")
    assert relatorio.num(10, 0) == "10"


def test_formato_hora():
    assert relatorio.hora(datetime(2026, 11, 19, 5, 0)) == "05h"
    assert relatorio.hora(datetime(2026, 11, 19, 12, 36)) == "12h36"


def test_periodo_no_se_redondea_para_arriba(dia_perfeito):
    """Caso real 23/11: 5,8 s se mostraba como '6 s' aunque aplicaba el techo."""
    item = {"registro": {**dia_perfeito, "swell_periodo": 5.8}}
    assert "período 5 s" in relatorio.descrever_swell(item)
